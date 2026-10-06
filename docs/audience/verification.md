# Verification evidence — Audience Engagement Lab

Build session: 6 October 2026. Source data are historical 2010–2011 observations, not current customer activity.

## Data and model evidence

- Official UCI HTTPS CSV downloaded, 45,038,760 bytes, pinned SHA-256 recorded in `results.json` and verified by the downloader and builder. The checksum is an observed pin, not a publisher signature.
- 541,909 source lines reconcile exactly with first-reason exclusions, conflicting invoice quarantine and 391,106 kept positive item lines. Aggregation yields 18,502 invoices and 4,336 known customers.
- Boundary tests show a purchase at the prediction cutoff enters the outcome, not history; changing its future amount leaves historical features unchanged. Incomplete future windows fail explicitly.
- Fixed July/September/November snapshots contain 1,968/1,920/2,459 customers. Training-only scaler tests verify future transform calls cannot change its fit.
- Actual November logistic ROC-AUC 0.692867 versus recency 0.553481; average precision 0.666036 versus 0.469406. Top-fifth precision 0.725610 versus 0.502033, each 492 customers. No synthetic target labels or threshold tuning.
- Customer bootstrap uses 300 paired resamples and seed17; gain interval [0.112615, 0.165771]. This covers November sampling only, not causal uplift or training uncertainty.

## App and browser checks

- Aggregate reports work with no Qwen; missing report/weights return503; invalid references return502. No raw source customer keys appear in the public report. CSV exports contain fictional cases only.
- Browser exercised live full-cohort and customer-history slice filters, September/November selection, territory-filtered fictional CSV, 390px mobile layout, and preserved Procedure Studio/Membership interfaces. No page errors.
- Static dashboard checked with all requests outside its static-server origin blocked: measured results, filters and fictional export work; new Qwen generation stays disabled. No live backend dependency.
- Exact startup helper `PORT=8004 bash scripts/start_audience.sh` was executed and its report endpoint verified. Dependency compatibility check passed. Existing pinned source downloader safely reused the verified source.
- Local Qwen generated the saved example in 33.71seconds on CPU including initialization. Its original wording and author edits are preserved in `example-brief.json`. Numeric-format validation bugs were reproduced before fixing; separate tests cover comma-separated counts and sentence-final decimals. Passing those checks is not semantic certification.

## Publication limits

The user's external Codespace is a separate machine. Pushing GitHub does not pull or restart that server. GitHub Pages publishes only the static snapshot. Deployment and external availability are recorded separately after verification; a local browser pass alone is not proof of publication.
