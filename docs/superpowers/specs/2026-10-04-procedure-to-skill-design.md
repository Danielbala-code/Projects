# Procedure-to-Skill Studio: portfolio demo design

Status: proposed design for user review. Application implementation has not started.

## Purpose and success

Build a small, understandable tool that demonstrates translating an approved business procedure into a reviewed workflow and portable AI skill. The user wants an interview portfolio project relevant to Vinarchy's Automation & AI Analyst role, with code and releases on GitHub. Each stage requires the user's greenlight. The target is approximately one hour of active implementation for a focused demo, with review pauses and external access changes separate.

Vinarchy publicly describes re-collecting and re-auditing Scope 1, 2 and 3 emissions data after its merger. This provides reporting context, not an internal SOP or proof of the prototype's savings. The first demonstration uses an explicitly fictional electricity-reporting intake procedure. It neither calculates emissions nor assigns emissions scopes.

Success means a nontechnical person can load the example, understand its required information, inspect supporting source passages, review the workflow, check a sample submission, and download the resulting skill. We must measure what works and identify limits rather than claim automatic conversion of every procedure or suitability for every industry.

Business source: https://vinarchy.com/pages/sustainability

## Scope

The first version supports one declared reporting template. Its required information is site name, period start, period end, electricity usage, unit, reporting owner and an evidence attachment. Supported validation checks are missing information, valid calendar dates, end date on or after start date, finite non-negative usage, the permitted unit `kWh`, and presence of an evidence attachment. The application does not check that the attachment's contents prove the reported numbers. A human performs that review.

Provide three fictional sample submissions: complete, missing evidence and incompatible unit/date. A source procedure can be a text PDF, plain text or Markdown. The demo supports at most 10 PDF pages or 100,000 extracted characters, with a 5 MB file limit. Scanned/image-only PDFs receive a clear explanation; OCR is future work.

The workflow engine should be separated from the electricity template so other reviewed schemas can be added later. The initial release must identify its supported workflow rather than advertise arbitrary-document interpretation.

## Nontechnical user flow

1. **Choose a procedure.** Load the fictional example or upload a supported document. Show its name, page count and a clear sample-data label.
2. **Review the checklist.** Display the reporting fields and validation requirements from the selected template as a draft. Each item includes suggested source passages, which the owner can inspect and select. Missing support is marked for review. Similarity does not approve an item.
3. **Approve the workflow.** The owner confirms which requirements apply. Export requires the included requirements and checks to have selected source references and an explicit review acknowledgement. This demo records that review action; it does not establish enterprise identity or approval permissions.
4. **Check a submission.** Enter reporting information and attach evidence. Return specific correction messages and a submission summary. A complete submission is labelled complete and awaiting human evidence review, not audited or externally accepted.
5. **Download.** Export the reviewed skill package and a submission result. A downloadable checklist is useful to users who do not use an AI agent.

Use familiar interface labels: Choose procedure, Review checklist, Supporting source, Approve workflow, Check submission and Download. Keep model settings and implementation terminology out of this flow.

## What retrieval and embeddings do

Retrieval means finding a source passage relevant to a requirement. An embedding is a numeric representation used to compare meaning. MiniLM can suggest a passage about a person responsible for submitting information when the checklist calls that field a reporting owner.

The core workflow does not require an embedding model. It uses extracted source text, a declared template, human review and explicit validation rules. Basic keyword search provides a working source-navigation baseline.

The optional MiniLM feature improves source suggestions. It does not generate a procedure, establish that a passage satisfies a requirement, derive arbitrary validation rules, or assess whether an evidence attachment is accurate. The business owner reviews the mapping; validation runs from the approved schema.

A vector database is unnecessary for this demo's small per-document collection. Keep passage vectors in memory and rank them with cosine similarity. Suggestions retain exact page/source references. Avoid interpreting similarity as a confidence percentage.

## Proposed stack and components

| Component | Choice and responsibility |
|---|---|
| Interface | Simple HTML/CSS/JavaScript served by the application; no frontend build system required |
| HTTP API | FastAPI; typed inputs and bounded uploads |
| PDF adapter | Pinned Skill Seekers 3.10.0 structured page extraction; consume page text and metadata, ignoring programming-code heuristics |
| Workflow engine | Small explicit reporting schema and deterministic validators; separate from the template |
| Skill compiler | Build `SKILL.md`, source references and a workflow manifest from reviewed requirements |
| Package export | Reuse Skill Seekers' packaging when appropriate, preserving licence notices; keep its default developer-documentation generator out of the business flow |
| Optional evidence matcher | MiniLM CPU inference with ONNX Runtime and the model tokenizer |
| Persistence | SQLite for procedure/workflow/submission metadata; local bounded storage for uploaded evidence |

Skill Seekers was installed and tested in scratch space. Its default PDF pipeline misclassified prose as code, and its generic quality scores did not detect business-template mismatch. This is why the adapter consumes clean page text and why the business compiler has its own requirements and verification. Upstream source remains unmodified.

Foundation record: `/workspace/research/2026-10-04-foundation-evaluation.md`.

## Model choice, costs and evaluation

Candidate: `Xenova/all-MiniLM-L6-v2`, an ONNX export of `sentence-transformers/all-MiniLM-L6-v2`, pinned to revision `751bff37182d3f1213fa05d7196b954e230abad9`. The q8 artifact is approximately 23 MB; verify its SHA-256 against repository metadata before use. The original model card specifies a 256-word-piece input limit. Passage splitting must respect tokenizer length and preserve page references.

Load the model once per process. Cache document vectors by document hash, model revision and chunking settings. The model's local inference has no provider token charges; compute, storage, hosting and downloads still have costs. No external generative model is required for the initial declared workflow.

The pinned artifact was downloaded and its size and SHA-256 verified. A scratch CPU smoke test produced finite 384-dimensional embeddings and matched a responsible-person query to the reporting-owner passage among three candidates. This confirms inference works here; it is not a retrieval-accuracy evaluation.

Before choosing semantic suggestions over the keyword baseline, compare both on a small labelled set with paraphrases, similar distractors, negated instructions and requirements absent from the document. Record correct-source retrieval in the top three, inappropriate suggestions, warm latency and memory. Include examples held out from threshold selection. If MiniLM is unsuitable, keep the useful core and evaluate a stronger retrieval model or reranker separately.

Published results and similar public demos support MiniLM as a candidate, not certification for reporting. See `/workspace/research/2026-10-04-model-selection-evidence.md`.

The optional matcher must display its actual availability. If the model cannot load, provide keyword source navigation and identify that semantic matching is unavailable. Do not silently call a paid model or describe fallback output as model inference.

## Data and source boundaries

- Treat uploaded document text as evidence, not instructions controlling the application or its tools.
- Preserve source identity, page number where available and the exact selected supporting text.
- Store only declared rule types and values; do not execute document text or user-provided expressions.
- Use generated identifiers and safe filenames for local storage and exports.
- Keep source documents and submissions out of Git. The public repository contains fictional fixtures only, with upstream notices.
- Core processing uses the application's machine. Source contents are not sent to a remote model service. Model downloads are a separate operation.
- This is a single-user portfolio demo. Organisation authentication, permission controls and confidential enterprise deployment are later work.

## API responsibilities

The API exposes health status, procedure ingestion, draft requirements/source suggestions, reviewed-workflow approval, submission checking and package export. Return structured results so a future Microsoft adapter can use the same workflow engine. Do not create a live Microsoft integration or claim tenant compatibility without a tested connection.

For export, enforce review state on the server. A skill package contains a short `SKILL.md`, a reviewed workflow manifest and supporting references. The skill explains its trigger, required information, checks, correction path and human evidence review. It does not claim authority to submit information externally.

## Meaningful verification

Verify the fictional procedure's required information and page references survive extraction and export. Exercise review-state enforcement and real multipart uploads through the API. Check a valid submission and failures for missing required data/evidence, invalid calendar dates, reversed periods, incompatible units and negative/non-finite usage. Empty or scanned PDFs, oversized uploads and unsafe filenames receive controlled errors.

Inspect the exported archive and execute the supported validation workflow rather than judging quality only from generated text. Verify the browser flow manually if browser tooling is available. Run a local HTTP request through ingestion, review, validation and export. Keep passed, failed, unrun and fallback outcomes distinct.

Model evaluation is separate from application validation. Successful explicit-rule checks do not prove retrieval quality; successful retrieval does not prove reporting accuracy.

## Hosting, integration and growth

Publish code, documentation, tests and releases on GitHub after the user's publication checkpoint. The Python/model-backed application needs a separate runtime; GitHub Pages alone will not execute this stack. Provide a simple CPU startup path and a container option if time permits. Public hosting is separate from the initial build and needs suitable account access.

The user has no Microsoft demo account. Document a future authenticated Power Automate/API connection while accurately marking it unimplemented. Production integration requires platform access, licensing and organisational controls.

Later stages may add reviewed workflow templates, multilingual retrieval, OCR, stronger-model drafting, organisation authentication, document-change review and audit exports. Changes in industry procedures require expert-reviewed schemas and fresh evaluation.

## Build budget and checkpoints

Keep the initial implementation focused on the sample procedure, one supported workflow, a working review/validation/export flow and relevant tests. Optional evidence matching must not prevent core progress. The one-hour active-build target is an estimate, not a guarantee of deployment or production readiness.

Current checkpoint: the user reviews this written design. After approval, use the writing-plans skill to create a short implementation plan and let the user choose its execution approach. The user has requested a greenlight before each subsequent build and publication stage; proceed only within the approved stage.
