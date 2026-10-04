# Skill Seekers Studio design

The user approved starting the GitHub/Codespaces demo after requesting broader Skill Seekers reuse. Build start: 2026-10-04 12:27 UTC. Target: one hour of active work. Publication is a separate review checkpoint. This supersedes the earlier electricity submission-validator proposal.

## Outcome

A process owner uploads a procedure, generates a draft AI skill, checks source passages alongside it, acknowledges review and downloads the package. Demonstrate using a clearly fictional electricity-reporting SOP relevant to Vinarchy's public reporting context. No claim of internal policy or compliance certification.

## Architecture

Skill Seekers 3.10.0 provides structured PDF extraction, custom WorkflowEngine stages, quality reporting and Claude-format packaging. Add a focused FastAPI browser interface for upload and business review. The existing HUD is beta, uses server-side source paths and offers broader project management than this flow needs.

One custom SOP drafting stage explicitly receives clean extracted page text and its returned draft is persisted. Ignore programming-code classifications, preserving page text. Upstream source remains unmodified.

Generation uses Apache-2.0 Qwen2.5-0.5B-Instruct Q4_K_M GGUF through llama-cpp-python on CPU. Pin revision `9217f5db79a29953eb74d5343926648285ec7e67` and SHA-256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`. Download the 491,400,032-byte model separately from source control. Use bounded context, deterministic temperature and JSON output. Evaluate a real sample before claiming suitability.

No embeddings, vector database or paid inference API are required initially. Whole-source drafting suits the bounded short SOP.

## Flow

1. Load the fictional sample or upload text PDF/TXT/Markdown.
2. View source pages; generate purpose and ordered steps with exact quotes/page references. Identify live generation, model unavailable or explicitly selected sample preview.
3. Inspect all steps and edit skill Markdown. Invalid citations block review approval. Editing resets approval.
4. Explicitly acknowledge review; export SKILL.md, full source references, draft manifest and review metadata through Skill Seekers packaging.

The preview is fixed sample content, clearly labelled. Uploads never silently use it. Generic quality scores do not establish source accuracy or completeness. Review metadata preserves original model mappings and records subsequent edits; human acknowledgement is not enterprise authentication.

## Boundaries

Limit sources to 5 MB, 10 PDF pages and 12,000 extracted characters. Reject without silent truncation. Reject blank, corrupt, scanned and non-UTF-8 inputs with actionable errors. Source text is data, never executable instructions. Use generated IDs and safe archive filenames. Keep bounded local sessions and temporary storage; documents, weights and exports remain outside Git. This is a single-user demo with a private Codespaces port, not a confidential enterprise deployment.

## GitHub delivery

Provide code, fictional fixtures, notices, tests, pinned requirements, Codespaces devcontainer and Actions checks. Python 3.12/CPU/no paid key. Codespaces runs while active; GitHub Pages cannot execute this backend. Actual provisioning/publication is reported separately from local cloud tests and follows the user's publication checkpoint.

## Verification

Test real extraction and archive contents, page references, invented citations, invalid inputs, explicit approval, approval reset, safe filenames, missing sessions and honest model availability. Run real local HTTP ingestion/draft/review/download. Evaluate Qwen on source-supported steps, omissions, latency and memory. Source support checks do not prove exhaustive coverage; human review remains required.
