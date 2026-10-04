# Procedure-to-Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Run a Skill Seekers document-to-skill demo on CPU with review and Codespaces setup.

**Architecture:** Skill Seekers extracts source pages, runs a custom SOP stage and packages the reviewed skill. FastAPI handles uploads, local Qwen drafting, review and download.

**Tech Stack:** Python 3.12, Skill Seekers 3.10.0, FastAPI, llama-cpp-python, Qwen2.5-1.5B-Instruct Q4_K_M GGUF, pytest.

**Spec:** `docs/superpowers/specs/2026-10-04-skill-seekers-studio-design.md`

## Global Constraints

- 5 MB, 10 PDF pages, 12,000 extracted characters; reject without silent truncation.
- Fictional sample only in Git; no paid API requirement or silent sample fallback.
- Exact source support and explicit acknowledgement before export; edits reset approval.
- Pin model revision/checksum from spec; weights stay outside Git.
- The user's start-now instruction authorizes this build; publication remains a checkpoint.

## Review Focus

- Fabricated citations block approval (Task 1).
- Corrupt/scanned/non-UTF-8/oversized sources get useful errors (Tasks 1/2).
- Unknown sessions get 404; unavailable models never masquerade as generation (Task 2).
- Edits reset approval; filenames cannot inject archive paths (Task 2).
- Generation failures preserve source and allow retry (Tasks 2/3).

### Task 1: Source and skill pipeline

**Files:** `studio/pipeline.py`, `studio/workflows/sop.yaml`, `samples/electricity-reporting.md`, `tests/test_pipeline.py`, `requirements.txt`, `THIRD_PARTY_NOTICES.md`.

**Interfaces:** `extract_source(content: bytes, filename: str) -> list[dict]`; `build_draft(pages: list[dict], transport: object) -> dict`; `validate_draft(draft: dict, pages: list[dict]) -> list[str]`; `package_skill(skill_dir: Path, output_dir: Path) -> Path`.

- [x] Write extraction/citation/packaging tests; run pytest and observe missing-behavior failures.
- [x] Implement clean page extraction, explicit WorkflowEngine context/output handling, fixture and notices.
- [x] Verify real PDF/archive outputs and commit pipeline.

### Task 2: Local model and browser review

**Files:** `studio/model.py`, `studio/app.py`, `studio/static/index.html`, `studio/static/app.js`, `studio/static/style.css`, `tests/test_app.py`.

**Interfaces:** `LocalModel.call(prompt: str, max_tokens: int) -> str`; `create_app(model: object | None = None) -> FastAPI`; HTTP ingestion/draft/review/export consume Task 1.

- [x] Write multipart HTTP tests for availability, approval/export and missing sessions; observe failures.
- [x] Implement bounded loading, explicit preview, source-visible review and server-enforced approval.
- [x] Run tests plus real Qwen sample; inspect source support/omissions; commit application.

### Task 3: Reproducible cloud delivery

**Files:** `.devcontainer/devcontainer.json`, `.github/workflows/checks.yml`, `scripts/download_model.py`, `README.md`, `.gitignore`, `docs/verification.md`.

**Interfaces:** downloader emits verified GGUF; `python -m uvicorn studio.app:app --host 0.0.0.0 --port 8000` serves app; CI runs pytest without model download.

- [x] Test checksum/failure cleanup before writing downloader.
- [x] Add install/start instructions, private Codespaces port and CI; run suite/HTTP walkthrough.
- [x] Record evaluation/limits, commit and obtain whole-branch review.
- [x] Present runnable demo for publication checkpoint.

## Final verification

Completed in the selected cloud checkout. The rejected 0.5B candidate was replaced by the pinned 1.5B model after real quality checks. Independent review defects were reproduced and fixed. See `docs/verification.md` for 18 passing tests, 8 passing subtests, actual model/browser checks and fresh installation evidence. GitHub publication remains the next user checkpoint.
