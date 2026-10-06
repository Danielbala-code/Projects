"""Single-user development interface for reviewed business skills."""
import copy
import hashlib
import json
import shutil
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask
from skill_seekers.cli.quality_checker import SkillQualityChecker

from .model import LocalModel
from .pipeline import Draft, MAX_BYTES, extract_source, build_draft, validate_draft, render_skill, package_skill

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT/'samples'/'electricity-reporting.md'


class DraftRequest(BaseModel):
    mode: Literal['generate', 'preview'] = 'generate'


class EditRequest(BaseModel):
    draft: Draft
    revision: int = Field(ge=0)
    markdown: str | None = Field(default=None, max_length=24_000)


class ApproveRequest(BaseModel):
    acknowledged: bool = False
    revision: int = Field(ge=0)


def create_app(model: object | None = None) -> FastAPI:
    app = FastAPI(title='Procedure-to-Skill Studio', docs_url=None, redoc_url=None)
    backend = model if model is not None else LocalModel()
    sessions = {}
    state_lock = threading.RLock()
    generation_lock = threading.Lock()

    def available():
        return bool(getattr(backend, 'available', True))

    def get_session(pid):
        with state_lock:
            item = sessions.get(pid)
            if not item or time.monotonic()-item['created'] > 3600:
                sessions.pop(pid, None)
                raise HTTPException(404, 'This session is missing or expired. Reload the procedure.')
            return item

    def public(item):
        return {k: v for k, v in item.items() if k not in {'created', 'original_draft'}}

    def ingest(content, filename, sample=False):
        try:
            pages = extract_source(content, filename)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        with state_lock:
            now = time.monotonic()
            for pid in list(sessions):
                if now-sessions[pid]['created'] > 3600:
                    del sessions[pid]
            if len(sessions) >= 32:
                raise HTTPException(429, 'Demo session limit reached. Restart the server or wait for sessions to expire.')
            pid = uuid.uuid4().hex
            item = {'id': pid, 'filename': Path(filename.replace('\\', '/')).name[:120], 'pages': pages, 'sample': sample, 'source_sha256': hashlib.sha256(content).hexdigest(), 'created': now, 'draft': None, 'markdown': '', 'citation_errors': [], 'approved': False, 'mode': None, 'revision': 0}
            sessions[pid] = item
            return public(item)

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'foundation': 'Skill Seekers 3.10.0', 'model': 'Qwen2.5-1.5B-Instruct Q4_K_M', 'model_available': available(), 'hosting': 'single-user development demo', 'session_ttl_seconds': 3600}

    @app.post('/api/sample')
    def sample():
        return ingest(SAMPLE.read_bytes(), SAMPLE.name, sample=True)

    @app.post('/api/procedures')
    async def upload(file: UploadFile):
        content = await file.read(MAX_BYTES+1)
        await file.close()
        return ingest(content, file.filename or 'document.txt')

    @app.get('/api/procedures/{pid}')
    def procedure(pid: str):
        return public(get_session(pid))

    @app.post('/api/procedures/{pid}/draft')
    def draft(pid: str, request: DraftRequest):
        with state_lock:
            item = get_session(pid)
            starting_revision = item['revision']
        if request.mode == 'preview':
            if not item['sample']:
                raise HTTPException(400, 'Preview applies only to the fictional sample. Your upload needs live generation.')
            steps = []
            for line in item['pages'][0]['text'].splitlines():
                if line[:1].isdigit() and '. ' in line:
                    quote = line.split('. ', 1)[1]
                    steps.append({'action': quote, 'page': 1, 'quote': quote})
            result = {'purpose': 'Collect a consistent monthly electricity report for human review.', 'steps': steps}
            mode = 'sample-preview'
            elapsed = 0
        else:
            if not available():
                raise HTTPException(503, 'Local model unavailable. Download the model, or explicitly choose the fictional sample preview.')
            if not generation_lock.acquire(blocking=False):
                raise HTTPException(409, 'The local model is busy. Retry when the current draft finishes.')
            started = time.monotonic()
            try:
                result = build_draft(item['pages'], backend)
            except Exception as exc:
                raise HTTPException(502, 'Draft generation failed. Source is preserved; retry or inspect the server setup.') from exc
            finally:
                generation_lock.release()
            elapsed = round(time.monotonic()-started, 2)
            mode = 'local-model'
        with state_lock:
            item = get_session(pid)
            if item['revision'] != starting_revision:
                raise HTTPException(409, 'The draft changed while generation ran. Your saved edits were kept. Reload before retrying.')
            item.update(draft=result, original_draft=copy.deepcopy(result), markdown=render_skill(result), citation_errors=validate_draft(result, item['pages']), approved=False, mode=mode, generation_seconds=elapsed, revision=item['revision']+1)
            item.pop('reviewed_at', None)
            return public(item)

    @app.put('/api/procedures/{pid}/draft')
    def edit(pid: str, request: EditRequest):
        with state_lock:
            item = get_session(pid)
            if not item['draft']:
                raise HTTPException(409, 'Generate a draft before editing it.')
            if request.revision != item['revision']:
                raise HTTPException(409, 'A newer draft exists. Reload and review it before saving.')
            data = request.draft.model_dump()
            markdown = request.markdown if request.markdown is not None else render_skill(data)
            if len(markdown.strip()) < 100:
                raise HTTPException(400, 'The skill is too short. Keep its procedure and review guidance.')
            item.update(draft=data, markdown=markdown, citation_errors=validate_draft(data, item['pages']), approved=False, revision=item['revision']+1)
            item.pop('reviewed_at', None)
            return public(item)

    @app.post('/api/procedures/{pid}/approve')
    def approve(pid: str, request: ApproveRequest):
        with state_lock:
            item = get_session(pid)
            if not request.acknowledged:
                raise HTTPException(400, 'Acknowledge source accuracy, coverage and your edits before approving.')
            if request.revision != item['revision']:
                raise HTTPException(409, 'A newer draft exists. Reload and review it before approving.')
            if not item['draft'] or validate_draft(item['draft'], item['pages']):
                raise HTTPException(409, 'Resolve missing or unsupported source citations before approving.')
            item.update(approved=True, reviewed_at=datetime.now(timezone.utc).isoformat())
            return public(item)

    @app.get('/api/procedures/{pid}/download')
    def download(pid: str):
        with state_lock:
            item = copy.deepcopy(get_session(pid))
        if not item['approved']:
            raise HTTPException(409, 'Review and approve this draft before downloading.')
        td = Path(tempfile.mkdtemp(prefix='studio-export-'))
        try:
            skill = td/'procedure-skill'; (skill/'references').mkdir(parents=True); (skill/'assets').mkdir()
            (skill/'SKILL.md').write_text(item['markdown'], encoding='utf-8')
            source = '\n\n'.join(f"## Page {p['page']}\n\n{p['text']}" for p in item['pages'])
            (skill/'references'/'source.md').write_text(source, encoding='utf-8')
            review = {'acknowledged': True, 'reviewed_at': item['reviewed_at'], 'revision': item['revision'], 'source_sha256': item['source_sha256'], 'generation_mode': item['mode'], 'fictional_sample': item['sample'], 'original_draft': item['original_draft'], 'reviewed_draft': item['draft'], 'limitations': 'Demo acknowledgement only. Exact quotes do not establish semantic accuracy or complete source coverage.'}
            (skill/'assets'/'review.json').write_text(json.dumps(review, indent=2), encoding='utf-8')
            quality = SkillQualityChecker(skill).check_all()
            (skill/'assets'/'quality.json').write_text(json.dumps({'score': quality.quality_score, 'meaning': 'Generic structural quality only; not business correctness.', 'errors': quality.errors, 'warnings': quality.warnings}, default=str, indent=2), encoding='utf-8')
            archive = package_skill(skill, td/'export')
            return FileResponse(archive, filename='reviewed-procedure-skill.zip', media_type='application/zip', background=BackgroundTask(shutil.rmtree, td))
        except Exception:
            shutil.rmtree(td, ignore_errors=True)
            raise

    from membership.app import create_membership_app
    app.mount('/membership', create_membership_app(backend), name='membership-lab')
    from audience.app import create_audience_app
    app.mount('/audience', create_audience_app(backend), name='audience-lab')
    app.mount('/', StaticFiles(directory=ROOT/'studio'/'static', html=True), name='interface')
    return app


app = create_app()
