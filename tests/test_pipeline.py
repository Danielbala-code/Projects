import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import pymupdf as fitz

from studio.pipeline import extract_source, build_draft, validate_draft, package_skill, source_passages, render_skill


def pdf_bytes(*pages):
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_text((40, 40), text)
    content = doc.tobytes()
    doc.close()
    return content


class PipelineTests(unittest.TestCase):
    def test_pdf_keeps_prose_and_page_references(self):
        pages = extract_source(pdf_bytes('The owner must attach meter evidence.', 'A reviewer must approve the report.'), '../../procedure.pdf')
        self.assertEqual([p['page'] for p in pages], [1, 2])
        self.assertIn('owner must attach', pages[0]['text'])
        self.assertIn('reviewer must approve', pages[1]['text'])

    def test_invalid_sources_have_actionable_errors(self):
        for content, name, message in [(b'', 'a.txt', 'empty'), (b'bad', 'a.pdf', 'PDF'), (pdf_bytes(''), 'a.pdf', 'scanned'), (b'\xff', 'a.txt', 'UTF-8'), (b'x'*12001, 'a.md', '12,000'), (b'x', 'a.exe', 'PDF'), (b'x'*(5*1024*1024+1), 'a.txt', '5 MB'), (pdf_bytes(*(['page']*11)), 'a.pdf', '10 pages')]:
            with self.subTest(name=name, message=message), self.assertRaisesRegex(ValueError, message):
                extract_source(content, name)

    def test_mixed_scanned_pdf_cannot_silently_lose_a_source_page(self):
        doc = fitz.open()
        doc.new_page().insert_text((40, 40), 'The coordinator records the site name.')
        image = fitz.open(); image.new_page().insert_text((40, 40), 'Human approval is required.')
        pixmap = image[0].get_pixmap()
        page = doc.new_page(); page.insert_image(page.rect, pixmap=pixmap)
        content = doc.tobytes(); doc.close(); image.close()
        with self.assertRaisesRegex(ValueError, 'scanned'):
            extract_source(content, 'mixed.pdf')

    def test_custom_workflow_receives_source_and_returns_draft(self):
        pages = [{'page': 1, 'text': 'Attach the meter evidence to the report.'}]
        class Transport:
            def call(self, prompt, **kwargs):
                if pages[0]['text'] not in prompt:
                    raise AssertionError('Missing actual source')
                return json.dumps({'purpose': 'Reporting', 'steps': [{'action': 'Attach evidence.', 'page': 1, 'quote': pages[0]['text']}]})
        draft = build_draft(pages, Transport())
        self.assertEqual(draft['steps'][0]['action'], 'Attach evidence.')
        self.assertEqual(validate_draft(draft, pages), [])

    def test_fabricated_citations_and_empty_drafts_fail(self):
        pages = [{'page': 1, 'text': 'Attach the meter evidence to the report.'}]
        invalid = {'purpose': 'Reporting', 'steps': [{'action': 'Submit.', 'page': 2, 'quote': 'Submit without checking the figures.'}]}
        self.assertTrue(validate_draft(invalid, pages))
        self.assertTrue(validate_draft({'purpose': 'Reporting', 'steps': []}, pages))
        self.assertTrue(validate_draft({'purpose': 'Reporting', 'steps': [{'action': 'Invent a rule.', 'page': 1, 'quote': ' '*12}]}, pages))

    def test_selected_source_ids_copy_exact_quotes_from_original_pages(self):
        pages = [{'page': 1, 'text': 'Attach meter evidence to the report.'}, {'page': 2, 'text': 'A reviewer must approve the report.'}]
        class Transport:
            def call(self, prompt, **kwargs):
                return json.dumps({'purpose': 'Reporting', 'steps': [{'source_id': 2, 'action': 'Get reviewer approval.'}]})
        draft = build_draft(pages, Transport())
        self.assertEqual(draft['steps'][0]['page'], 2)
        self.assertEqual(draft['steps'][0]['quote'], pages[1]['text'])
        self.assertEqual(validate_draft(draft, pages), [])

    def test_unknown_source_id_does_not_invent_evidence(self):
        class Transport:
            def call(self, prompt, **kwargs):
                return json.dumps({'purpose': 'Reporting', 'steps': [{'source_id': 999, 'action': 'Get reviewer approval.'}]})
        with self.assertRaisesRegex(ValueError, 'source'):
            build_draft([{'page': 1, 'text': 'Attach meter evidence to the report.'}], Transport())

    def test_numbered_steps_preserve_order_and_use_their_own_evidence(self):
        pages = [{'page': 1, 'text': 'Demo context.\n\nPurpose: review.\n\n1. Attach meter evidence to the report.\n2. A reviewer must approve the report.'}]
        calls = []
        class Transport:
            def call(self, prompt, **kwargs):
                calls.append(prompt)
                return json.dumps({'purpose': 'Reporting', 'steps': [{'source_id': 1, 'action': 'Review this instruction.'}]})
        draft = build_draft(pages, Transport())
        self.assertEqual(len(draft['steps']), 2)
        self.assertEqual(draft['steps'][0]['quote'], 'Attach meter evidence to the report.')
        self.assertEqual(draft['steps'][1]['quote'], 'A reviewer must approve the report.')
        self.assertEqual(len(calls), 2)

    def test_skill_keeps_authoritative_details_when_ai_clarification_is_short(self):
        quote = 'The coordinator records the site name and both reporting dates.'
        text = render_skill({'purpose': 'Reporting', 'steps': [{'action': 'Record the site name.', 'page': 1, 'quote': quote}]})
        self.assertIn(quote, text)
        self.assertIn('authoritative', text.lower())

    def test_packaging_uses_skill_seekers_archive_format(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); skill = root/'skill'; skill.mkdir()
            (skill/'SKILL.md').write_text('# Reviewed fictional skill\n')
            (skill/'references').mkdir()
            (skill/'references'/'source.md').write_text('Exact supporting source.')
            archive = package_skill(skill, root/'export')
            with zipfile.ZipFile(archive) as z:
                self.assertIn('SKILL.md', z.namelist())
                self.assertEqual(z.read('references/source.md'), b'Exact supporting source.')

if __name__ == '__main__':
    unittest.main()
