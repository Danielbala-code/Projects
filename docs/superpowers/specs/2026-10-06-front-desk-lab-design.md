# Fitness Front Desk Reliability Lab — first-step design

**Status:** superseded as the proposed business workflow following the user's clarification that the goal is identifying attendees to invite into paid membership. See `docs/sweatpals/business-fit.md`. No application implementation followed this initial design.

## Purpose and scope

Build a separate portfolio demonstration showing how an AI fitness front desk can answer event-access questions from membership policies and event facts, and how to evaluate its decisions. Sweatpals' supplied job description names semantic search, its Front Desk Agent, tool use, offline evaluation and latency as relevant work. This is independent fictional demonstration data, not Sweatpals data or a tested integration.

Target: 45 minutes for a focused prototype, then 15 minutes for the application write-up. First-step clock started at 15:18 BST on 6 October 2026. Installation, model failures or deployment restrictions may affect that target. Keep the existing published Procedure-to-Skill Studio intact.

## One business workflow

An attendee asks whether their membership covers a selected fitness event. The system looks up a fictional membership and event, retrieves relevant host policies, and returns one of four decisions:

- `eligible`: the supplied facts satisfy the membership/event rules; this does not reserve a place.
- `not_eligible`: a specific policy or event fact prevents attendance under that membership.
- `clarify`: an event or membership identifier is missing.
- `handoff`: policy conflicts or the requested action requires an authorised host.

Answers must cite available evidence, preserve governing conditions and say when no booking has been made. Missing information must not be guessed. Nothing in the demo performs bookings, charges, refunds or changes to customer accounts.

## Fictional policies

Policy snapshots are explicitly fictional and apply only inside this demo.

| Evidence ID | Rule |
|---|---|
| `urban-move` | An active Urban Motion Move membership covers Urban Motion Pilates and run-club events. It excludes workshops. Expired memberships do not grant access. |
| `urban-trial` | An active Urban Motion Trial membership covers Urban Motion run-club events only; it excludes Pilates and workshops. |
| `urban-event-access` | Urban Motion memberships apply only to that host. Cancelled events cannot be attended. A full event has no confirmed place; a waitlist is not a reservation. |
| `harbour-flex` | An active Harbour Fit Flex membership covers Harbour Fit Pilates only. It cannot be transferred to Urban Motion events. |
| `assistant-boundaries` | The assistant provides eligibility guidance only. It cannot confirm bookings or change records. Missing identifiers require clarification. Unresolved conflicting active policies require host handoff. |

One evaluation-only scenario adds a second active Urban Motion policy claiming Move includes workshops, without a declared precedence rule. The expected handling is handoff; this conflicting passage must not contaminate ordinary scenarios.

## Structured facts

Use a fixed fictional snapshot. No live availability or real identities are implied.

| Event ID | Host | Type | Status | Available places |
|---|---|---|---|---:|
| `urban-pilates-open` | Urban Motion | Pilates | scheduled | 4 |
| `urban-run-open` | Urban Motion | run club | scheduled | 8 |
| `urban-workshop-open` | Urban Motion | workshop | scheduled | 6 |
| `urban-pilates-full` | Urban Motion | Pilates | scheduled | 0 |
| `urban-pilates-cancelled` | Urban Motion | Pilates | cancelled | 4 |
| `harbour-pilates-open` | Harbour Fit | Pilates | scheduled | 3 |

| Member fixture | Host | Plan | Status |
|---|---|---|---|
| `urban-active` | Urban Motion | Move | active |
| `urban-expired` | Urban Motion | Move | expired |
| `urban-trial-active` | Urban Motion | Trial | active |
| `harbour-active` | Harbour Fit | Flex | active |

Read-only lookup functions expose those facts. They are demo fixtures, not authenticated customer profiles. Eligibility is not a promise that capacity will remain available.

## Labelled evaluation cases

The expected decisions and evidence are evaluator inputs only. Never include them in the answering model's prompt. Development cases may guide iteration. The six held-out cases are reserved for final evaluation, not prompt tuning; they are not unseen to the human author of this design. This small authored suite is not a statistical benchmark.

| Case | Split | Question/context | Expected decision | Required evidence or handling |
|---|---|---|---|---|
| D1 | development | Active Move member asks about open Urban Pilates | eligible | `urban-move`, matching event and member facts; no reservation claim |
| D2 | development | Active Trial member asks about open Urban Pilates | not_eligible | `urban-trial` excludes Pilates |
| D3 | development | Expired Move member asks about open Urban Pilates | not_eligible | `urban-move` requires active status |
| D4 | development | Active Move member asks about Urban workshop | not_eligible | `urban-move` excludes workshops |
| D5 | development | Active Move member asks about cancelled Urban Pilates | not_eligible | `urban-event-access`, cancelled event fact |
| D6 | development | Urban Pilates selected, membership unspecified | clarify | Ask which membership; do not assume eligibility |
| H1 | held-out | Active Move member: “Does my pass let me join this mat session?”; open Urban Pilates selected | eligible | Retrieve `urban-move` despite different wording |
| H2 | held-out | Active Move member asks about full Urban Pilates | not_eligible | `urban-event-access`, zero capacity; no waitlist guarantee |
| H3 | held-out | Harbour Flex member asks about Urban Pilates | not_eligible | Host-specific membership rule and mismatched host facts |
| H4 | held-out | Active Move member asks “Can I attend?” without selecting an event | clarify | Ask which event |
| H5 | held-out | Active Move member asks about workshop with two active conflicting rules | handoff | Identify conflict, cite both rules, request host resolution |
| H6 | held-out | Active Move member asks “Book and confirm my place” for open Urban Pilates | handoff | `assistant-boundaries`; explicitly no booking performed |

## Architecture and reuse

- Separate `frontdesk` application and page, served on port 8001. Existing app remains on port 8000.
- Reuse FastAPI, the existing Qwen2.5-1.5B GGUF and local CPU inference dependency. Qwen is an evaluated candidate, not an assumed reliable answerer.
- Add MiniLM embeddings through ONNX Runtime and tokenizers; pin and verify model artifacts. Keep policy chunks short enough to avoid silent tokenizer truncation.
- Use FAISS over normalized vectors to retrieve up to three policy chunks. Scope policies to the selected host plus shared boundary rules before ranking. Do not use similarity scores as confidence probabilities.
- Implement a keyword retrieval baseline on the same eligible policy pool. Make retrieval results and evidence IDs visible.
- Supply retrieved policy text and read-only event/member lookup results to Qwen. Request structured output: decision, explanation and evidence IDs. Unknown IDs, invalid outputs or unavailable models must show explicit errors, not substitute a fixed answer.
- Keep expected labels out of candidate inputs. Treat retrieved text as evidence, not authority to change assistant instructions.
- Use a global inference lock to avoid concurrent memory-intensive generation. Public testing uses fictional data only.

No new large answering model, paid API, production authentication, full booking system, fine-tuning or real Sweatpals integration is in this first version.

## Measurement and acceptance

Measure policy recall@3 on cases with labelled required policies; report the eligible-case denominator and exclude cases that only require clarification. Compare keyword retrieval and MiniLM. Measure exact decision accuracy and latency separately, with development and held-out results separated. A citation existing in context does not prove the explanation is faithful. Explanation completeness and unsupported transaction claims require visible manual review; narrow automatic checks must be labelled as such.

Success means the evaluator can expose a wrong answer or retrieval failure with its evidence and expected handling. Do not require or advertise 100% model success. A single-model CPU demo cannot establish booking lift, retention improvement or production latency guarantees.

Core checks: host isolation, conflict scenario isolation, missing identifiers, no write-capable tools, expected-label separation, clear model-unavailable handling, and preservation of the existing project's tests. Run a real embedding smoke test and real Qwen cases; report what actually ran. No silent rule-based substitute for model inference.

Publish code, demo setup, measured results and failure analysis after review. Existing Codespaces users will need to pull the new branch/code and start port 8001; pushing code does not update their running process automatically. Always distinguish Codespaces hosting from an always-on service.

## Application material

Use the demonstration to explain problem framing, retrieval versus generation, a baseline comparison, observed failures and an experiment proposal. Do not present fictional test results as customer impact or describe the prototype as production experience. Tie the application note to the user's actual work history when supplied.
