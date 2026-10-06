# Audience Engagement & Experiment Lab

## Purpose and agreed direction

Create one interview portfolio prototype for EXL's international fan analytics role and Sky's OTT data-science role. Reuse the existing FastAPI application and local Qwen instance. The user chose GitHub Codespaces as the runtime; permanent free hosting is outside this build.

The business workflow is: inspect content engagement, understand customer lifecycle segments, estimate return engagement, and prepare an eligible audience for a controlled campaign test. This is an independent prototype, with no company affiliation or access to either company's customer systems.

## Two explicit data layers

**Real public content:** the raw workbook from Zenodo record 20719982, downloaded and verified in this environment. It contains 75,216 source rows across five European football leagues. The earlier MarketCast audit identified mostly league-owned channels, malformed rows and incomplete 2025 coverage. Use the five primary league channels and publication cohorts in 2023–2024. Show actual cleaning counts rather than hard-code the earlier audit's result.

Source: Abuín-Penas, Corbacho-Valencia and Pérez Seoane, *Dataset: YouTube video metadata of the Big Five European football leagues*, DOI 10.5281/zenodo.20719982, CC-BY-4.0. Raw file: 25,056,941 bytes; SHA-256 `6f04b4fec20eab1e6f8bfbdfb435533dee9d4fb87d3802a534e3009e2c9fd2d7`.

Preserve IDs, channel, publication time, duration and observed views/likes/comments. Quarantine malformed identifiers, conflicting records and unusable required values. Treat missing likes/comments as unknown. Rates require a positive view denominator and observed components. Report video counts, median observed views and median interactions per 1,000 views with their denominators. These are snapshot counters for publication cohorts, not measured monthly viewing or fanbase growth. Do not use the selected, duplicate-containing 150-row coded workbook as representative evidence.

**Synthetic customer journeys:** a reproducible, seeded fixture with customer identifiers, explicitly assigned UK/Italy/Ireland territories, organisation ownership, consent, signup time, activity events, recent contact and observation dates. All customer fields and outcomes are fictional. Public video data contains no customer identity, viewer territory or consent; do not link simulated customers to actual viewers or derive their territory from league location or content language.

## Analysis and modelling

Use visible SQL joins, aggregations and window functions for lifecycle segments and reporting. Define segments from observed pre-index activity: new, engaged, occasional and dormant. Document thresholds as demo choices.

Predict whether a synthetic customer returns within the next 14 days. Use pre-index recency, activity frequency and tenure; exclude identifiers, future events and outcome fields from predictors. Train a small logistic regression with train-only preprocessing and compare it with a training-prevalence baseline. Use separate chronological observation cohorts, ensuring training outcome windows finish before evaluation observations begin. Display sample counts, class balance, ROC-AUC when defined and Brier score. Report actual results, including a failure to beat the baseline. These metrics establish simulation behaviour, not real customer prediction accuracy or retention lift.

Campaign preparation excludes wrong-organisation records, opt-outs, unknown consent and customers contacted inside a declared 14-day cooldown. Assign eligible customers reproducibly to test/control groups within territory and segment, without duplicate recipients or overlapping groups. Export labelled fictional audience records. No campaign is sent. A return-propensity score is not incremental benefit from outreach; test/control allocation prepares a future experiment and establishes no business lift.

## Qwen's role

Qwen2.5-1.5B-Instruct remains a pretrained, local language model. It receives a compact set of already-computed report facts, definitions and limitations, then drafts a stakeholder explanation with fact references. SQL/Python calculate metrics; logistic regression supplies predictions. Qwen does not calculate the authoritative results, train the predictive model, resolve consent or execute campaigns.

Generation is explicit and optional. Show missing-model and generation failures. Keep the computed report usable independently, with a separate labelled factual explanation. Structured output and selected claim checks do not certify semantic correctness; the analyst reviews the wording.

## Delivery and boundaries

Mount the new interface at `/audience/` in the existing process, sharing Qwen and preserving `/` and `/membership/`. Provide content reporting, customer segments, model comparison, campaign preview/export and an optional stakeholder brief. Bound filter inputs and exports. Keep downloaded source files, runtime database and model weights outside Git; retain reproducible download/build scripts, SQL, provenance and compact measured outputs.

The implementation budget is 30 minutes for the focused prototype, with priority on the data pipeline, metrics, evaluated model and audience export. No new embedding model, agent framework, production authentication, live delivery, distributed warehouse integration or additional hosting account is required. Document how approved first-party data and a warehouse adapter would replace the simulation; claim only integrations actually exercised.

## Acceptance evidence

- Verify source artifact integrity, cleaning reasons and report denominators.
- Demonstrate that feature preparation excludes post-index activity and that preprocessing uses training data only.
- Test consent/ownership/cooldown exclusions, test/control disjointness and deterministic assignment.
- Record actual predictive baseline comparison on the reserved chronological cohort.
- Verify computed reports remain available when Qwen is absent or fails.
- Exercise the browser flow and CSV export, and run the existing projects' regression tests.
- Publish tested code and an application note describing real-data and simulation boundaries; updating GitHub does not restart the user's separate Codespace.
