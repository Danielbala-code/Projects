# Audience Engagement & Experiment Lab implementation
Spec: docs/superpowers/specs/2026-10-06-audience-engagement-design.md

Global constraints: one-hour focused build; preserve existing apps; no raw customers in public reports; no sending campaigns; all figures measured. MIND download access failed (HF 401, original Azure 409). Use the spec's real UCI Online Retail alternative rather than substitute synthetic model outcomes. This is repeat purchase, not churn or streaming engagement. User authorized implementation and publication in this session.

## Task 1: Real data and reproducible audit
Produce private SQLite invoices and public aggregate report. Download official UCI CSV, record byte count and SHA256, pin verified artifact for subsequent reproduction. Parse numeric/date formats strictly; separate cancellations, missing customers, invalid/nonpositive amounts, exact duplicates; quarantine inconsistent invoice identity. SQL creates customer snapshots using only prior 90 days and labels using next 30 days. Fixed train 2011-07-01, validation 2011-09-01, final test 2011-11-01; complete outcome window required.
Interfaces: build output aggregate JSON, private invoice SQLite; model consumes snapshot arrays with named features.
Tests first: invoice aggregation, leakage boundary, complete windows, cleaning reasons. Expected RED import/missing behavior, then GREEN. Run full pytest suite before commit.

## Task 2: Defensible modelling and campaign controls
Compare train prevalence, recency rank, fixed L2 logistic regression (C=1, scaler train only). Evaluate ROC-AUC, average precision, top-20-percent precision with deterministic ties, logistic Brier and calibration, same cohort denominators. Keep validation and test separately visible; frozen design before results. Holdout bootstrap confidence interval and slices where both labels exist. Customer correlation and domain limits explicit. Fictional fixture tests ownership, consent, 14-day cooldown, duplicate identities; deterministic disjoint test/control within territory/segment. No real customer IDs exported.
Interfaces: aggregate JSON with provenance/audit/cohorts/models/facts and fictional experiment rows.
Tests first: metric denominators, chronological feature invariance, deterministic/disjoint campaign groups and exclusions. Expected RED then GREEN. Build on real artifact, inspect actual results, run full suite, commit.

## Task 3: Live app, static companion and delivery
Mount /audience before existing root static app. Reports are precomputed; optional shared local Qwen generates referenced stakeholder brief with explicit failure states. Factual explanation always available. Static docs/index.html and shared assets work with no backend; include filter, measured comparison, model decisions, fictional CSV export and source limitations. No real customer IDs served. Prepare GitHub Pages publication workflow/settings, verify browser desktop/mobile, offline static flow, API failure modes, existing apps. Document warehouse/API replacement path and reproducible startup.
Interfaces: public JSON same schema for live and static; API /api/report, /api/brief, /api/campaign.csv.
Tests first: missing snapshot 503, reports without LLM, brief errors/reference checks, CSV fiction only; expected RED then GREEN. Full suite and functional browser checks. One fresh read-only whole-branch review, one important-fix pass, publish authorized code and verify available hosting.

Review focus: snapshot boundary and incomplete labels; duplicate/invoice cleaning assumptions; preprocessing fit only train; interpretation of scores and observational business claims; raw data exposure; campaign controls and CSV injection; static/live distinction; cross-app regression; accessible mobile UI.
