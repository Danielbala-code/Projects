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


class SelectedStep(BaseModel):
    source_id: int = Field(ge=1, le=128)
    action: str = Field(min_length=3, max_length=600)


class SelectedDraft(BaseModel):
    purpose: str = Field(min_length=3, max_length=600)
    steps: list[SelectedStep] = Field(min_length=1, max_length=16)


def source_passages(pages: list[dict]) -> list[dict]:
    passages = []
    for page in pages:
        for paragraph in re.split(r'\n\s*\n|\n(?=\s*\d{1,2}[.)]\s+)', page['text']):
            numbered = bool(re.match(r'^\s*\d{1,2}[.)]\s+', paragraph))
            paragraph = re.sub(r'^\s*\d{1,2}[.)]\s+', '', paragraph.strip())
            if paragraph.startswith('#') or len(paragraph) < 12:
                continue
            normalized = re.sub(r'\s+', ' ', paragraph)
            sentences = [normalized] if numbered else re.split(r'(?<=[.!?])\s+(?=[A-Z])', normalized)
            for sentence in sentences:
                if len(sentence) > 1000:
                    raise ValueError('A source instruction exceeds 1,000 characters. Split it into shorter steps.')
                if 12 <= len(sentence) <= 1000:
                    passages.append({'source_id': len(passages)+1, 'page': page['page'], 'quote': sentence, 'numbered': numbered})
    if not passages or len(passages) > 128:
        raise ValueError('This source needs shorter sentences or paragraphs for drafting.')
    return passages


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
                for page in doc:
                    if not page.get_text().strip() and (page.get_images() or page.get_drawings()):
                        raise ValueError('This PDF contains a scanned or image-only page. OCR is not enabled; upload a fully text-based procedure.')
            with tempfile.TemporaryDirectory(prefix='studio-source-') as td:
                source = Path(td)/'source.pdf'; source.write_bytes(content)
                extractor = PDFExtractor(str(source), use_cache=False)
                try:
                    extractor.extract_all()
                    pages = [{'page': p['page_number'], 'text': p['text'].strip()} for p in extractor.pages]
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
    passages = source_passages(pages)
    numbered = [p for p in passages if p['numbered']]
    if numbered:
        if len(numbered) > 16:
            raise ValueError('This demo supports at most 16 numbered instructions.')
        steps = []
        purpose = None
        for passage in numbered:
            single = dict(passage, source_id=1)
            selected = _run_draft([single], transport)
            if len(selected['steps']) != 1:
                raise ValueError('The model must return one draft per source instruction. Retry drafting.')
            # The source mapping is structural, never selected by the model here.
            steps.append({'action': selected['steps'][0]['action'], 'page': passage['page'], 'quote': passage['quote']})
            purpose = purpose or selected['purpose']
        for page in pages:
            match = re.search(r'(?im)^Purpose:\s*(.+)', page['text'])
            if match:
                purpose = match.group(1).strip(); break
        return Draft.model_validate({'purpose': purpose, 'steps': steps}).model_dump()
    return _run_draft(passages, transport)


def _run_draft(passages: list[dict], transport: object) -> dict:
    engine = WorkflowEngine(Path(__file__).parent/'workflows'/'sop.yaml')
    engine.enhancer = transport
    source = '\n'.join(f"[{p['source_id']}] {p['quote']}" for p in passages)
    result = engine.run({}, context={'source': source})
    try:
        if result.get('steps') and 'source_id' in result['steps'][0]:
            selection = SelectedDraft.model_validate(result)
            lookup = {p['source_id']: p for p in passages}
            steps = []
            for step in selection.steps:
                if step.source_id not in lookup:
                    raise ValueError('The model selected an unknown source passage. Retry drafting.')
                ref = lookup[step.source_id]
                steps.append({'action': step.action, 'page': ref['page'], 'quote': ref['quote']})
            result = {'purpose': selection.purpose, 'steps': steps}
        return Draft.model_validate(result).model_dump()
    except ValidationError as exc:
        raise ValueError('The model did not return a complete source-grounded draft. Retry or use the labelled sample preview.') from exc


def validate_draft(draft: dict, pages: list[dict]) -> list[str]:
    try:
        parsed = Draft.model_validate(draft)
    except ValidationError:
        return ['Draft needs a purpose and 1–16 steps with actions, page numbers and supporting quotes.']
    normalize = lambda s: re.sub(r'\s+', ' ', s).strip()
    sources = {p['page']: normalize(p['text']) for p in pages}
    errors = []
    for i, step in enumerate(parsed.steps, 1):
        quote = normalize(step.quote)
        if len(quote) < 12 or step.page not in sources or quote not in sources[step.page]:
            errors.append(f'Step {i}: supporting quote was not found on page {step.page}. Review the source and regenerate.')
    return errors


def render_skill(draft: dict) -> str:
    title = 'Reviewed procedure'
    content = ['---', 'name: procedure-reporting', 'description: "Follow the reviewed reporting procedure and consult its source references."', '---', '', f'# {title}', '', '## When to use', '', draft['purpose'], '', '## Procedure', '', 'The source requirement under each instruction is authoritative. A clarification can omit details. Follow the full source requirement; ask the process owner if the clarification conflicts with it.', '']
    for i, step in enumerate(draft['steps'], 1):
        content.extend([f"{i}. {step['action']}", '', f"   Source requirement: {step['quote']}", '', f"   Reference: [page {step['page']}](references/source.md#page-{step['page']})", ''])
    content.extend(['## Review and escalation', '', 'Consult references/source.md for the full procedure. If information is missing or ambiguous, ask the process owner. Do not invent rules or submit information externally without authorisation.', '', 'This package records a demo review acknowledgement; it does not certify compliance or establish organisational approval.', ''])
    return '\n'.join(content)


def package_skill(skill_dir: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return get_adaptor('claude').package(skill_dir, output_dir/'procedure-skill.zip')
