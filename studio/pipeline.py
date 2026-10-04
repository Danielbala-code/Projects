"""Source extraction, grounded workflow drafting and Skill Seekers export."""
import json
import re
import tempfile
from pathlib import Path

import pymupdf
from pydantic import BaseModel, Field, ValidationError
from skill_seekers.cli.pdf_extractor_poc import PDFExtractor
from skill_seekers.cli.enhancement_workflow import WorkflowEngine
from skill_seekers.cli.adaptors import get_adaptor

MAX_BYTES = 5 * 1024 * 1024
MAX_CHARS = 12_000


class Step(BaseModel):
    action: str = Field(min_length=3, max_length=600)
    page: int = Field(ge=1, le=10)
    quote: str = Field(min_length=12, max_length=1000)


class Draft(BaseModel):
    purpose: str = Field(min_length=3, max_length=600)
    steps: list[Step] = Field(min_length=1, max_length=16)


def extract_source(content: bytes, filename: str) -> list[dict]:
    if not content:
        raise ValueError('The source is empty. Choose a text document.')
    if len(content) > MAX_BYTES:
        raise ValueError('Source exceeds 5 MB. Choose a smaller document.')
    suffix = Path(filename).suffix.lower()
    if suffix not in {'.pdf', '.txt', '.md'}:
        raise ValueError('Choose a text PDF, TXT or Markdown file.')
    if suffix == '.pdf':
        try:
            with pymupdf.open(stream=content, filetype='pdf') as doc:
                if doc.needs_pass:
                    raise ValueError('Unlock this PDF before uploading it.')
                if len(doc) > 10:
                    raise ValueError('PDF exceeds 10 pages. Choose a shorter procedure.')
                if not any(page.get_text().strip() for page in doc):
                    raise ValueError('This PDF is empty or scanned. OCR is not enabled; upload text instead.')
            with tempfile.TemporaryDirectory(prefix='studio-source-') as td:
                source = Path(td)/'source.pdf'; source.write_bytes(content)
                extractor = PDFExtractor(str(source), use_cache=False)
                try:
                    extractor.extract_all()
                    pages = [{'page': p['page_number'], 'text': p['text'].strip()} for p in extractor.pages if p['text'].strip()]
                finally:
                    if extractor.doc is not None and not extractor.doc.is_closed:
                        extractor.doc.close()
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('Could not read this PDF. Upload a valid, unlocked text PDF.') from exc
    else:
        try:
            text = content.decode('utf-8-sig').strip()
        except UnicodeDecodeError as exc:
            raise ValueError('Text files must use UTF-8 encoding.') from exc
        pages = [{'page': 1, 'text': text}] if text else []
    if not pages:
        raise ValueError('The source is empty. Choose a text document.')
    if sum(len(p['text']) for p in pages) > MAX_CHARS:
        raise ValueError('Source exceeds 12,000 extracted characters. Choose a shorter procedure.')
    return pages


def build_draft(pages: list[dict], transport: object) -> dict:
    engine = WorkflowEngine(Path(__file__).parent/'workflows'/'sop.yaml')
    engine.enhancer = transport
    source = '\n\n'.join(f"PAGE {p['page']}\n{p['text']}" for p in pages)
    result = engine.run({}, context={'source': source})
    try:
        return Draft.model_validate(result).model_dump()
    except ValidationError as exc:
        raise ValueError('The model did not return a complete draft. Retry or use the labelled sample preview.') from exc


def validate_draft(draft: dict, pages: list[dict]) -> list[str]:
    try:
        parsed = Draft.model_validate(draft)
    except ValidationError:
        return ['Draft needs a purpose and 1–16 steps with actions, page numbers and supporting quotes.']
    normalize = lambda s: re.sub(r'\s+', ' ', s).strip()
    sources = {p['page']: normalize(p['text']) for p in pages}
    errors = []
    for i, step in enumerate(parsed.steps, 1):
        if step.page not in sources or normalize(step.quote) not in sources[step.page]:
            errors.append(f'Step {i}: supporting quote was not found on page {step.page}. Review the source and regenerate.')
    return errors


def render_skill(draft: dict) -> str:
    title = 'Reviewed procedure'
    content = ['---', 'name: procedure-reporting', 'description: "Follow the reviewed reporting procedure and consult its source references."', '---', '', f'# {title}', '', '## When to use', '', draft['purpose'], '', '## Procedure', '']
    for i, step in enumerate(draft['steps'], 1):
        content.extend([f"{i}. {step['action']}", f"   Source: [page {step['page']}](references/source.md#page-{step['page']})", ''])
    content.extend(['## Review and escalation', '', 'Consult references/source.md for the full procedure. If information is missing or ambiguous, ask the process owner. Do not invent rules or submit information externally without authorisation.', '', 'This package records a demo review acknowledgement; it does not certify compliance or establish organisational approval.', ''])
    return '\n'.join(content)


def package_skill(skill_dir: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return get_adaptor('claude').package(skill_dir, output_dir/'procedure-skill.zip')
