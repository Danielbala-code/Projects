# Evaluation record — 6 October 2026

## Scope

One fictional Urban Motion host, three fictional USD monthly plans and 22 fictional attendees. Fourteen are eligible for ranking; eight are excluded. Manual relevance grades and ten expected-plan choices live in a separate evaluation file and are read only after ranking. They never enter ranking or generation prompts.

The 11 development and 11 reserved cases are author-created, not independent human judgements or real outcomes. Seven eligible attendees appear in each split. Weights were declared before the measured comparison; the reserved results were not used to tune them. The term `held_out` in the JSON denotes those reserved fixture cases, not a statistically convincing generalisation claim.

## Actual MiniLM execution

Pinned Xenova/all-MiniLM-L6-v2 quantized ONNX on CPU, mean pooling with attention mask, L2 normalisation and FAISS inner-product search. Model size 22,972,370 bytes; tokenizer 711,661 bytes. Both size and SHA-256 verify before inference.

| Reserved split measurement | Keyword baseline | MiniLM + FAISS |
|---|---:|---:|
| Precision@5 (grade ≥ 2) | 0.80 | 0.80 |
| NDCG@5 | 1.00 | 1.00 |
| Expected plan matches | 5/5 | 5/5 |
| First measured ranking latency | 0.76 ms | 358.17 ms |

The development split had the same quality metrics. [Raw measurements](measured-ranking.json) include both splits and ranked IDs. The MiniLM number includes initialization and plan indexing; this is a single environment run, not a warmed, repeated hardware benchmark. The UI measures each requested run again.

During final review, the pinned tokenizer's built-in fixed 128-token padding/truncation was found to conflict with custom masking. Two failing regressions reproduced padded tokens counted as real text and 300-token input silently truncated. The encoder now disables both artifact settings before explicit padding/masking and the 256-token rejection check. The table and raw measurements above were rerun after that correction and replace the invalid initial measurements.

**Decision:** keep keywords as default. This fixture does not show a quality gain from embeddings. Frequency and recency dominate the declared weights, the catalogue is tiny and activity eligibility restricts possible plans. Broader independently labelled cases, language variation and a larger catalogue would be necessary to assess semantic matching properly. Do not reinterpret perfect synthetic NDCG as measured conversion accuracy.

## Real local Qwen trials

Three semantic-mode invitation requests were run through the actual HTTP API with the pinned Qwen2.5-1.5B Q4_K_M model on CPU:

| Attendee | Initial outcome | Wall time |
|---|---|---:|
| Alex | Draft accepted by narrow checks | 19.22 s |
| Jordan | Draft rejected; HTTP 502; nothing sent | 14.04 s |
| Nora | Draft accepted by narrow checks | 15.20 s |

These three checks are a smoke sample, not a generation-success-rate estimate. JSON-schema decoding enforces shape, not truth. Initial output for Alex and Nora retained price and visit limits but still needed editing: wordy greetings, sales language and unnecessary repetition. The requested word limit was not guaranteed by the initial prompt.

The rejected Jordan draft said “feel free to reach out”; it did not promise a free membership. The checker treated the isolated word “free” as a benefit claim. A failing API regression reproduced this, and the correction normalises that specific idiom before checking. A second test confirms that “feel free ... free guest passes” still fails. After correction, the same Jordan draft passed through the real browser/API in 23.14 seconds (first-use Qwen load included); reviewed download and edit-reset were verified in that walkthrough. [Actual AI interface screenshot](../assets/membership-ai-draft.png) preserves the displayed wording. This is a bounded false-positive correction, not an expansion of membership benefits.

The checker detects selected forbidden benefits/transaction terms and numbers outside the approved facts. It is intentionally described as a narrow guard, not complete semantic verification. It can miss swapped quantities, paraphrased unsupported benefits or omissions; it can reject harmless words in context. Human review remains required. No automatic fallback converts a failed inference into claimed AI success.

The labelled factual template is a separate user choice. Review acknowledgement and download happen in the browser; the demo does not verify reviewer identity, preserve an audit database or send campaigns.

## Functional verification

- The complete Python regression suite (35 tests plus 8 subtests at this checkpoint) covers the original document app and membership exclusions, missing dependencies, invalid modes, unknown/ineligible recipients, credit-capped savings, factual templates, unsupported model claims and fact-only prompts.
- A schema-transport test checks that the shared model adapter preserves the original procedure schema and accepts the invitation schema.
- A real Chromium walkthrough verifies shortlist loading, both-mode comparison, template editing/review/download, approval reset after edits, the original studio route, no JavaScript page errors, and no horizontal overflow at a 390-pixel viewport.
- The artifact downloader verifies reusable files; dependency consistency and both JavaScript syntax checks pass.

These checks establish the portfolio workflow in this environment. They do not establish a production deployment, business lift, an authenticated Sweatpals connection or reliability across arbitrary customer data.

## Production work still required

Approved event/member/plan/consent contracts; host-level access controls; current entitlement validation; data minimisation; campaign delivery integration and contact-budget enforcement; generation evaluation on independently reviewed cases; retries/timeouts and telemetry; durable review records; outcome attribution; randomised uplift tests and retention monitoring. The ranking weights and contact cooldown are demo choices, not stated Sweatpals policies.
