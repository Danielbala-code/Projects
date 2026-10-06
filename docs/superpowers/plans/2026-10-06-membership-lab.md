# Membership Opportunity Lab Implementation Plan

> Implement inline with superpowers:executing-plans. The user authorised completing the revised workflow; no further planning handoff is needed.

**Goal:** Publish a host-facing fictional membership shortlist with baseline/embedding comparison and source-grounded invitation drafts.
**Spec:** `docs/sweatpals/business-fit.md`
**Architecture:** Mount `/membership` inside the existing FastAPI process, sharing its Qwen instance. A separate membership package owns fixtures, ranking, MiniLM/FAISS, evaluation and UI. This avoids two simultaneous 2 GB Qwen processes in a 4 GB Codespace.
**Stack:** Existing Python/FastAPI/Qwen; ONNX Runtime 1.23.2, tokenizers 0.22.1, FAISS CPU 1.12.0; no PyTorch.

## Global constraints
- Fictional data only; no sending campaigns, subscriptions or authenticated customer records.
- Exclude active members, wrong-host attendees, opted-out people and outreach within 14 days. Unknown consent/status requires review.
- Membership scores are transparent heuristics, not conversion probabilities. Embeddings compare text relevance only.
- Expected relevance labels remain outside ranker and model inputs. Report synthetic benchmark limitations and actual failures.
- Existing wine app remains functional. Downloaded weights and original user uploads stay outside Git.

## Review focus
- Host isolation and opt-out/cooldown exclusions: API tests.
- Savings cannot include visits beyond plan credits or unlisted activities: pricing tests.
- Missing embedding/model must produce explicit errors, not disguised inference: API tests.
- Untrusted text/unknown evidence IDs and unsupported transaction claims: draft tests.
- Shared local-model refactor must preserve SOP output schema: existing suite plus schema transport test.

## Task 1: Facts, rules and baseline
Files: `membership/data.json`, `membership/engine.py`, `membership/evaluation.json`, `tests/test_membership.py`.
Interfaces: `shortlist(mode, search=None) -> dict`, `evaluate(result) -> dict`, `facts_for(attendee_id, result) -> dict`.
- [x] Write failing mounted API and exclusion/pricing expectations.
- [x] Add declared fictional dataset, transparent scores, exclusions and labels kept out of ranking.
- [x] Verify baseline, pricing and existing suite; commit.

## Task 2: MiniLM and grounded draft/API
Files: `membership/embeddings.py`, `membership/app.py`, `scripts/download_embeddings.py`, `studio/model.py`, `studio/app.py`, `requirements-membership.txt`.
Interfaces: `MiniLM.similarities(query, plans) -> list[float]`; `LocalModel.complete(system, prompt, schema, max_tokens) -> str`; mounted GET health/shortlist and POST draft.
- [x] Add failure checks before implementing unavailable inference and draft constraints.
- [x] Implement verified tokenizer/model download, normalized mean pooling and FAISS; do not silently truncate.
- [x] Mount application and share Qwen, preserving old `call` contract; draft is unapproved text with visible evidence.
- [x] Run real embeddings and real invitation generation; save measurements, failures and limitations.

## Task 3: Interface, delivery and review
Files: `membership/static/`, README, devcontainer/setup helper, workflow and `docs/sweatpals/evaluation.md`, application note.
- [x] Build shortlist, evidence/detail drawer, editable draft, review-before-local-download and evaluation comparison.
- [x] Run API/unit suite, browser walkthrough/mobile check and dependency check.
- [x] Obtain one fresh whole-branch review, fix Important defects with RED→GREEN checks.
- [x] Publish updated code on project branch and main, verify public repository. Explain pulling/restarting the existing Codespace; publishing code does not restart it.
