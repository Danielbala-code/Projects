# Verification record

Build started 2026-10-04 at 12:27 UTC in the selected Codex cloud checkout. GitHub/Codespaces publication is a separate checkpoint. These results describe this machine, not an already deployed public service.

## Application checks

- Python 3.12; CPU inference with four model threads; no GPU or paid model API.
- Automated suite: **18 tests and 8 subtests passed** using `python -m pytest -q` in both the scratch environment and fresh repository-local `.venv`.
- Real Skill Seekers PDF extraction, page references, custom workflow context and ZIP packaging exercised.
- Invalid UTF-8, empty/corrupt/scanned/oversized sources and mixed text/image-only PDF pages covered.
- Exact quote validation rejects invented and whitespace-only quotes.
- Export requires explicit approval of the current revision. Edits invalidate it. Tests cover stale-tab approval and generation racing saved human edits.
- Verified model-download size/checksum, existing-file reuse and failure cleanup tested without remote downloads in the suite.
- Node syntax, shell syntax and devcontainer JSON/Actions YAML parsing checked.
- Dependency check: no broken requirements in the scratch installation.

## Real local generation

Pinned model: [Qwen2.5-1.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF), revision `91cad51170dc346986eccefdc2dd33a9da36ead9`, Q4_K_M. The 1,117,320,736-byte download matched SHA-256 `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`.

| Fictional fixture | Source steps retained | Exact-quote errors | Measured generation |
|---|---:|---:|---:|
| Electricity reporting | 7 | 0 | 17.25 seconds, including first model load |
| Supplier onboarding | 3 | 0 | 5.96 seconds with model already loaded |

Peak process RSS was approximately **2,095 MiB** in this two-fixture run. A separate live browser run took **16.31 seconds** for the electricity sample. These small measurements are not hosting guarantees or accuracy percentages. Four CPU threads were used; two-core Codespaces performance remains unmeasured.

The 0.5B candidate produced unreliable quotes and omitted operational instructions. Whole-source 1.5B drafting also mislinked passages. The final numbered-procedure pipeline preserves source instructions/order and clarifies each instruction separately. Full exact source requirements are included in SKILL.md, not only in reference files.

Manual inspection still found paraphrase omissions: one electricity clarification omitted reporting dates; another omitted the review decision. Role names were sometimes omitted. The full authoritative source requirements retain these details. **Zero citation errors does not mean zero semantic errors.** Human review remains required, especially for unnumbered documents. This is a two-fixture demonstration, not a held-out quality benchmark or domain certification.

## Browser and HTTP checks

Headless Chromium exercised sample ingestion, **actual local-model generation**, source review, acknowledgement, ZIP download and edit invalidation. The downloaded ZIP contained:

- `SKILL.md`
- `references/source.md`
- `assets/review.json`
- `assets/quality.json`

All seven full electricity source requirements were present in the exported skill. Review metadata identified `local-model`, the source hash and acknowledged revision. Sample preview was separately tested and labelled as no inference.

Desktop screenshot inspected; mobile viewport checked at 390 × 844 with no horizontal overflow. No browser page errors were observed. A current screenshot is in [assets/studio.png](assets/studio.png).

## Independent review

A separate reviewer inspected the implementation and reproduced four Important defects: omitted scanned pages, generation overwriting saved edits, stale approval and whitespace quotes passing validation. Each received a reproducing test, was fixed and passed the suite. The model-presence badge now states that verification happens on first use; it does not claim a corrupt file is a loaded model.

## Installation and hosting limits

The scratch install, CPU build and runtime were verified. The initial compiler setting referred to unavailable Clang; selecting GCC/G++ fixed it. `bash scripts/setup.sh` also succeeded in a fresh repository-local `.venv`; its test suite passed all 18 tests and 8 subtests, and `pip check` found no broken requirements. The repository downloader also completed and verified the default model file. A final HTTP walkthrough using this fresh `.venv` uploaded the supplier fixture, generated all three steps in 10.75 seconds including model load, approved the current revision and downloaded a ZIP containing the full source requirements.

Codespaces configuration and GitHub Actions checks are included. **At initial build completion**, Codespaces provisioning, GitHub Actions execution on GitHub and public hosting had not run; application code had not yet been pushed. The follow-up evidence below records subsequent publication and use. The cloud environment's reusable install/start instructions were saved as a draft; saving does not publish them or establish fresh-task restoration of local-only commits.

Model health reports file presence; checksum verification occurs on first inference. Confidential organisation deployment, authenticated reviewers, OCR, Microsoft integration and broad document-quality evaluation are future work.


## Publication and Codespaces follow-up

- Code published to procedure-to-skill-studio; [GitHub Actions run](https://github.com/Danielbala-code/Projects/actions/runs/37207797955) completed successfully for commit 580f51c8092bd88ff63943116578f179dbe91fd9.
- The owner provisioned a Codespace, completed dependency setup and downloaded the checksum-verified model. User-provided server logs and exported review metadata record use of the app with a real document.
- The owner set port 8000 to Public. An unauthenticated request to the public /api/health endpoint returned status ok, Skill Seekers 3.10.0 and model_available true. This indicates model-file presence; integrity/load checks still occur on generation.
- Public demo: https://effective-space-winner-9g7q6g66v6jh7569-8000.app.github.dev/ . GitHub may show its development-port notice. This is temporary Codespaces hosting, not an always-on service.
- [Full exported-package evaluation](evaluation/real-document-review.md) confirms source-text preservation but identifies main-skill omissions and quality-check limitations. Passing software tests does not establish procedural completeness.
