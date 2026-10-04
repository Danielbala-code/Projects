import io
import json
import unittest
import zipfile

from fastapi.testclient import TestClient
from studio.app import create_app


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

    def test_upload_generate_review_and_download_real_archive(self):
        pid = self.ingest()
        response = self.client.post(f'/api/procedures/{pid}/draft', json={'mode': 'generate'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['mode'], 'local-model')
        self.assertEqual(response.json()['citation_errors'], [])
        self.assertEqual(self.client.get(f'/api/procedures/{pid}/download').status_code, 409)
        self.assertEqual(self.client.post(f'/api/procedures/{pid}/approve', json={'acknowledged': False}).status_code, 400)
        self.assertEqual(self.client.post(f'/api/procedures/{pid}/approve', json={'acknowledged': True}).status_code, 200)
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
        self.client.post(f'/api/procedures/{pid}/approve', json={'acknowledged': True})
        data['draft']['steps'][0]['quote'] = 'A completely invented instruction.'
        result = self.client.put(f'/api/procedures/{pid}/draft', json={'draft': data['draft']})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()['citation_errors'])
        self.assertFalse(result.json()['approved'])
        self.assertEqual(self.client.post(f'/api/procedures/{pid}/approve', json={'acknowledged': True}).status_code, 409)

    def test_unavailable_model_never_silently_uses_preview(self):
        client = TestClient(create_app())
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
