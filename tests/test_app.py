import io
import json
import unittest
import zipfile
import threading
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from studio.app import create_app
from studio.model import LocalModel


SOURCE = 'The site coordinator attaches meter evidence to the report.'


class FixedTransport:
    def call(self, prompt, **kwargs):
        return json.dumps({'purpose': 'Review the electricity report.', 'steps': [{'action': 'Attach meter evidence.', 'page': 1, 'quote': SOURCE}]})


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(FixedTransport()))

    def ingest(self, content=SOURCE.encode(), name='../../source.md'):
        response = self.client.post('/api/procedures', files={'file': (name, content, 'text/plain')})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['id']

    def review(self, pid, acknowledged=True, revision=None):
        if revision is None:
            revision = self.client.get(f'/api/procedures/{pid}').json()['revision']
        return self.client.post(f'/api/procedures/{pid}/approve', json={'acknowledged': acknowledged, 'revision': revision})

    def test_upload_generate_review_and_download_real_archive(self):
        pid = self.ingest()
        response = self.client.post(f'/api/procedures/{pid}/draft', json={'mode': 'generate'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['mode'], 'local-model')
        self.assertEqual(response.json()['citation_errors'], [])
        self.assertEqual(self.client.get(f'/api/procedures/{pid}/download').status_code, 409)
        self.assertEqual(self.review(pid, False).status_code, 400)
        self.assertEqual(self.review(pid).status_code, 200)
        archive = self.client.get(f'/api/procedures/{pid}/download')
        self.assertEqual(archive.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(archive.content)) as z:
            self.assertIn('SKILL.md', z.namelist())
            self.assertIn(SOURCE, z.read('references/source.md').decode())
            meta = json.loads(z.read('assets/review.json'))
            self.assertTrue(meta['acknowledged'])
            self.assertEqual(meta['generation_mode'], 'local-model')
            self.assertFalse(any('..' in n or n.startswith('/') for n in z.namelist()))

    def test_changes_reset_approval_and_invalid_quotes_block_it(self):
        pid = self.ingest()
        data = self.client.post(f'/api/procedures/{pid}/draft', json={'mode': 'generate'}).json()
        self.review(pid)
        data['draft']['steps'][0]['quote'] = 'A completely invented instruction.'
        result = self.client.put(f'/api/procedures/{pid}/draft', json={'draft': data['draft'], 'revision': data['revision']})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()['citation_errors'])
        self.assertFalse(result.json()['approved'])
        self.assertEqual(self.review(pid).status_code, 409)

    def test_stale_tab_cannot_approve_an_unseen_revision(self):
        pid = self.ingest()
        original = self.client.post(f'/api/procedures/{pid}/draft', json={'mode': 'generate'}).json()
        original['draft']['steps'][0]['action'] = 'Attach the evidence after checking it.'
        saved = self.client.put(f'/api/procedures/{pid}/draft', json={'draft': original['draft'], 'revision': original['revision']})
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(self.review(pid, revision=original['revision']).status_code, 409)
        self.assertEqual(self.review(pid, revision=saved.json()['revision']).status_code, 200)

    def test_pending_generation_preserves_successfully_saved_review_edits(self):
        class BlockingTransport(FixedTransport):
            block = False
            started = threading.Event()
            release = threading.Event()
            def call(self, prompt, **kwargs):
                if self.block:
                    self.started.set(); self.release.wait(timeout=5)
                return super().call(prompt, **kwargs)
        transport = BlockingTransport(); client = TestClient(create_app(transport))
        pid = client.post('/api/procedures', files={'file': ('a.txt', SOURCE)}).json()['id']
        original = client.post(f'/api/procedures/{pid}/draft', json={'mode': 'generate'}).json()
        transport.block = True
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(client.post, f'/api/procedures/{pid}/draft', json={'mode': 'generate'})
            self.assertTrue(transport.started.wait(timeout=5))
            original['draft']['steps'][0]['action'] = 'A saved human correction.'
            saved = client.put(f'/api/procedures/{pid}/draft', json={'draft': original['draft'], 'revision': original['revision']})
            transport.release.set()
            self.assertEqual(saved.status_code, 200)
            self.assertEqual(future.result().status_code, 409)
        current = client.get(f'/api/procedures/{pid}').json()
        self.assertEqual(current['draft']['steps'][0]['action'], 'A saved human correction.')

    def test_unavailable_model_never_silently_uses_preview(self):
        with tempfile.TemporaryDirectory() as td:
            client = TestClient(create_app(LocalModel(Path(td)/'missing.gguf')))
        pid = client.post('/api/procedures', files={'file': ('custom.txt', SOURCE)}).json()['id']
        response = client.post(f'/api/procedures/{pid}/draft', json={'mode': 'generate'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(client.post(f'/api/procedures/{pid}/draft', json={'mode': 'preview'}).status_code, 400)
        sample = client.post('/api/sample').json()['id']
        preview = client.post(f'/api/procedures/{sample}/draft', json={'mode': 'preview'})
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.json()['mode'], 'sample-preview')

    def test_missing_sessions_bad_sources_and_failed_model_are_controlled(self):
        self.assertEqual(self.client.get('/api/procedures/missing').status_code, 404)
        self.assertEqual(self.client.post('/api/procedures', files={'file': ('a.txt', b'\xff')}).status_code, 400)
        class BrokenTransport:
            def call(self, prompt, **kwargs):
                raise RuntimeError('backend detail should not leak')
        client = TestClient(create_app(BrokenTransport()))
        pid = client.post('/api/procedures', files={'file': ('a.txt', SOURCE)}).json()['id']
        response = client.post(f'/api/procedures/{pid}/draft', json={'mode': 'generate'})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('backend detail', response.text)
        self.assertEqual(client.get(f'/api/procedures/{pid}').status_code, 200)

if __name__ == '__main__':
    unittest.main()
