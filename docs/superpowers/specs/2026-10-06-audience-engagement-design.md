# Audience Engagement & Experiment Lab

## Purpose and agreed direction

Create one interview portfolio prototype for EXL's international fan analytics role and Sky's OTT data-science role. Reuse the existing FastAPI application and local Qwen instance. The user chose GitHub Codespaces for the live runtime and subsequently requested a companion GitHub Pages site that remains viewable when that Codespace stops.

Revision proposed after the user requested real customer-journey data, realistic simulation rules and explicit model decisions. The recommended core is now real, logged content engagement and personalisation using Microsoft MIND-small, rather than an invented retention outcome. This dataset choice remains for user review. The workflow is: audit behavioural logs, compare content-ranking approaches, explain engagement patterns, and demonstrate controlled campaign preparation separately. This is an independent prototype, with no company affiliation or access to either company's customer systems.

## Implemented source decision

The user approved the one-hour focused implementation. Source preflight found MIND's linked Hugging Face archive requires access (HTTP401), and the original Azure archive returns409. The implementation therefore uses the real UCI Online Retail alternative already described below, with the domain change visible throughout the product. The MIND ranking sections below record the original proposal; they are superseded for this build by the following retail contract. No MIND download gate was bypassed.

**Actual target:** positive repeat-purchase invoice within 30 days among customers with a positive invoice in the preceding90 days. Item lines aggregate to invoices; missing identities, cancellation/nonpositive lines, exact duplicates and conflicting invoice metadata have visible exclusions. This does not measure subscription churn, streaming behaviour or incremental outreach benefit.

**Frozen design:** train at2011-07-01, validation at2011-09-01, reserved test at2011-11-01; complete future windows required. Train-only StandardScaler and L2 logistic regression C=1 use recency, log invoice count, log positive purchase value and observed tenure within the90-day window. Compare against training prevalence and recency ranking on identical cohorts using ROC-AUC, average precision and top-fifth precision; show Brier/calibration, country/history slices and paired customer-bootstrap uncertainty. No embeddings or retrieval are needed for these numeric features. These decisions were committed in the implementation plan before real-data model evaluation.

**Public boundary:** aggregate report and coefficients only, plus separate fictional UK/Ireland/Italy consent and experiment cases. Raw source, invoice database and customer-level predictions stay private/ignored. Qwen writes optional referenced prose; a saved original and author-reviewed example appears on Pages. The complete target budget is one hour; deployment checks and the external Codespace's update are distinguished from local success.

## Real journey dataset choice

**Recommended: Microsoft MIND-small.** Its published schema provides anonymous reader IDs, impression timestamps, ordered pre-impression reading histories, displayed article candidates, and clicked/non-clicked labels. The small release samples 50,000 readers from Microsoft News logs collected in 2019. It represents reading behaviour, not streaming watch time or the acquisition-to-subscription lifecycle. Readers in the parent collection were selected for at least five clicks over six weeks, so the population is not representative of every visitor or inactive customer.

The official project page and schema were inspected; download-host metadata was checked, but the archives have not yet been downloaded or audited here. The official page links a hosted copy of MIND-small, whose pinned dataset revision is `0f871bdfd1ac4029324a48722ec6d52d714ebf27`: train archive 52,953,372 bytes, SHA-256 `a966e5138ad103376e9817e02395719bf1c62ec56e6e98c30d46fbb991a7fafa`; validation archive 30,946,172 bytes, SHA-256 `b315cde1c9b9d45008b5a7c4b2e1f87647659f09f74892ae3899c0005d5d6155`.

Sources: https://msnews.github.io/ and https://github.com/msnews/msnews.github.io/blob/master/assets/doc/introduction.md. Microsoft Research License Terms permit non-commercial research, public demonstrations and reporting results, and prohibit redistributing the dataset or including a material portion in publications. Keep raw data and substantial extracts out of Git, Pages, downloads and public APIs. Publish code, aggregate findings and metrics; use a small fictional catalogue for the publicly downloadable example campaign. Dataset URLs may be expired; do not depend on fetching article bodies.

**Alternative: UCI Online Retail.** It has 541,909 transaction-line records, dates, customer identifiers, countries and cancellation indicators, under CC-BY-4.0. It would support a real repeat-purchase problem with careful invoice aggregation and complete outcome windows, but represents gift retail rather than content consumption. This is a distinct alternative, not another dataset to add to the same 30-minute core. Source: https://archive.ics.uci.edu/dataset/352/online+retail.

FastAPI is the web framework serving our analysis; it does not supply customer data. A source API or downloadable dataset supplies observations, and our FastAPI endpoints expose computed results.

## Two explicit data layers

**Real public content:** the raw workbook from Zenodo record 20719982, downloaded and verified in this environment. It contains 75,216 source rows across five European football leagues. The earlier MarketCast audit identified mostly league-owned channels, malformed rows and incomplete 2025 coverage. Use the five primary league channels and publication cohorts in 2023–2024. Show actual cleaning counts rather than hard-code the earlier audit's result.

Source: Abuín-Penas, Corbacho-Valencia and Pérez Seoane, *Dataset: YouTube video metadata of the Big Five European football leagues*, DOI 10.5281/zenodo.20719982, CC-BY-4.0. Raw file: 25,056,941 bytes; SHA-256 `6f04b4fec20eab1e6f8bfbdfb435533dee9d4fb87d3802a534e3009e2c9fd2d7`.

Preserve IDs, channel, publication time, duration and observed views/likes/comments. Quarantine malformed identifiers, conflicting records and unusable required values. Treat missing likes/comments as unknown. Rates require a positive view denominator and observed components. Report video counts, median observed views and median interactions per 1,000 views with their denominators. These are snapshot counters for publication cohorts, not measured monthly viewing or fanbase growth. Do not use the selected, duplicate-containing 150-row coded workbook as representative evidence.

**Limited synthetic campaign fixture:** reproducible cases with fictional customer identifiers, explicitly assigned UK/Italy/Ireland territories, organisation ownership, consent and recent contact. Neither MIND nor public video data supplies marketing consent or these customer territories. Do not attach invented attributes to actual anonymous readers, derive territory from content language, or export them as contactable people. MIND's core model evaluation uses its real click labels; the synthetic fixture tests business controls only.

The existing football workbook remains separate market/content context. It cannot be joined to MIND readers as if the two sources described the same audience. The focused build prioritises behavioural ranking and evaluation; extensive additional football reporting is an extension if it would exceed the time budget.

## Synthetic fallback rules

If the real-data route proves unavailable, obtain agreement before replacing it with a simulation. Document measured source distributions versus deliberately chosen stress scenarios. Generate event timelines first and derive outcomes from later events; do not assign labels directly from the score the model is intended to learn. Include heterogeneous activity, heavy-tailed frequency, intermittent gaps, cold starts, imperfect logging and cohort drift. Include explicit duplicate/conflicting identifiers, missing fields, late events, opt-outs and unknown consent as named test cases, without claiming their chosen prevalence matches a company.

Freeze generation assumptions, seeds, prediction time, splits and evaluation metrics before comparing models. Reserve a later cohort and a separately seeded or shifted scenario, and report all declared scenarios. Do not regenerate until results look good, rebalance evaluation to hide rare outcomes, or change thresholds after reading the reserved results. Synthetic performance establishes only behaviour under those simulation assumptions.

## Analysis and modelling

Use visible SQL joins, aggregations and window functions for impression-level reporting, history coverage, category engagement and data-quality investigation. Distinguish repeated impressions from duplicate keys and article IDs from reader IDs. Missing article metadata and blank histories require visible handling, not invented profiles. Repeated readers and correlated article candidates are not independent experimental subjects.

**Target:** rank the articles displayed in an impression so clicked articles appear higher. This is observed click prediction conditional on the logged candidate set, not subscription churn, guaranteed interest or incremental campaign response.

| Model/component | Decision and reason |
|---|---|
| Training-popularity ranking | Required non-personalised baseline. Uses only training click/exposure statistics; exposes whether personalisation adds value. Define smoothing and unseen-article handling before evaluation. |
| History/category and TF-IDF title similarity | Required transparent personalisation benchmark/features. Uses pre-impression history to compare content category and title words, is inexpensive on CPU and makes its limitations inspectable. |
| L2-regularised logistic regression | Small learned ranking model using popularity, history/category affinity and title-similarity features. Fast to train, explainable and proportionate to a 30-minute demo. Sort candidates by its learned scores. The model must earn inclusion against the baselines; scores are not calibrated purchasing or retention probabilities. |
| Existing MiniLM | Optional later comparison replacing word-based similarity with semantic similarity. Do not include it merely because weights are available; the previous project showed no measured gain on its fixture. |
| Qwen2.5-1.5B Q4_K_M | Optional language explanation of computed facts. It is not the click predictor, metric calculator or authority on audience eligibility. |

Keep each impression intact within a split, preserve the official train/validation distinction and audit timestamp boundaries before accepting a chronological claim. Fit TF-IDF and preprocessing only on article IDs observed in training histories/candidate sets; compute popularity from training outcomes only. Validation click labels must never enter histories or predictors. Use a deterministic, declared bounded subset if full processing exceeds the budget; display exact counts and selection rules. If a sports-focused slice is shown, define it from content/history available before the outcome, not by selecting successful clicks.

Report NDCG@5 and mean reciprocal rank over the same eligible validation impressions for every model, together with denominators and the treatment of missing metadata, no-click impressions and empty histories. Show a cold-start slice and avoid selecting a model on the reserved final cases. An optional impression-level bootstrap describes sampling variability in this logged dataset, not causal uplift. This observational benchmark cannot establish that a different ranking caused more clicks.

Campaign preparation uses only the separate fictional cases and excludes wrong-organisation records, opt-outs, unknown consent and customers contacted inside a declared 14-day cooldown. Assign eligible fictional customers reproducibly to test/control groups within territory and a declared segment, without duplicate recipients or overlapping groups. Export labelled fictional audience records. No campaign is sent. Observed click propensity is not incremental benefit from outreach; test/control allocation prepares a future experiment and establishes no business lift.

## Qwen's role

Qwen2.5-1.5B-Instruct remains a pretrained, local language model. It receives a compact set of already-computed report facts, definitions and limitations, then drafts a stakeholder explanation with fact references. SQL/Python calculate metrics; the ranking benchmarks and logistic regression supply predictions. Qwen does not calculate the authoritative results, train the predictive model, resolve consent or execute campaigns.

Generation is explicit and optional. Show missing-model and generation failures. Keep the computed report usable independently, with a separate labelled factual explanation. Structured output and selected claim checks do not certify semantic correctness; the analyst reviews the wording.

## Delivery and boundaries

Mount the new interface at `/audience/` in the existing process, sharing Qwen and preserving `/` and `/membership/`. Provide behavioural reporting, real-data ranking comparison, explicitly fictional campaign preview/export and an optional stakeholder brief. Bound filter inputs and exports. Keep downloaded source files, runtime database and model weights outside Git; retain reproducible download/build scripts, SQL, provenance and compact measured outputs.

Publish a companion static GitHub Pages dashboard containing generated reporting data, browser filters, the measured model comparison, provenance, sample campaign outputs and a reviewed example brief. It must work without contacting the Codespace. Label its build/snapshot time, real/synthetic data boundaries and example outputs. Link to the live Codespace separately for Python workflows and new Qwen generation; those actions require the server to be running. Pages does not execute the Python backend or Qwen. Preserve any existing Pages content and verify repository Pages configuration before choosing a deployment path. Do not invent an active Pages URL or claim deployment before it is verified.

The implementation budget is 30 minutes for the focused prototype, with priority on the data pipeline, metrics, evaluated model and audience export. Pages packaging uses the same generated outputs; activation is subject to repository settings and available GitHub permissions. No new embedding model, agent framework, production authentication, live delivery, distributed warehouse integration or additional hosting account is required. Document how approved first-party data and a warehouse adapter would replace the simulation; claim only integrations actually exercised.

## Acceptance evidence

- Verify source artifact integrity, cleaning reasons and report denominators.
- Demonstrate that history preparation excludes current-outcome labels, impressions remain intact within splits, and preprocessing/popularity use training data only.
- Test consent/ownership/cooldown exclusions, test/control disjointness and deterministic assignment.
- Record actual ranking baseline comparisons on the reserved validation impressions and cold-start slice; audit timestamps before claiming a temporal split.
- Verify computed reports remain available when Qwen is absent or fails.
- Exercise the browser flow and CSV export, and run the existing projects' regression tests.
- Verify the Pages dashboard and filters function with the live backend unavailable, and check deployed Pages and live Codespace independently.
- Publish tested code and an application note describing real-data and simulation boundaries; updating GitHub does not restart the user's separate Codespace.
