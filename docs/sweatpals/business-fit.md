# Sweatpals business-fit review — 6 October 2026

## Clarified user goal

Help hosts identify existing attendees to invite into a paid membership. This is attendee-to-member conversion, not acquisition of previously unknown users, existing-member eligibility support or churn prediction. It replaces the initial front-desk workflow as the proposed portfolio focus. No new application implementation has started.

## Public evidence reviewed

Read the public homepage, host offering, discovery page, catalogue, Austin discovery guide, Help Center, member guide, University index, paid-membership guide, campaign-segmentation guide, host analytics guide, waitlist guide, blog index and gym/studio product announcement. Did not access private dashboards, authenticated customer profiles, mobile app screens or checkout. Website guides and testimonials are company material, not independently audited performance evidence.

| Source | Relevant evidence |
|---|---|
| [Homepage](https://www.sweatpals.com/) and [catalogue](https://www.sweatpals.com/explore) | Event and community discovery support social fitness experiences; the consumer journey starts before paid membership |
| [Host offering](https://www.sweatpals.com/host) | Hosts create membership plans, collect signup/questionnaire data, manage members and use marketing support |
| [Help Center](https://help.sweatpals.com/) | Joining a community is distinct from buying a paid membership. Memberships can provide discounts or limited booking uses |
| [Paid memberships guide](https://university.sweatpals.com/paid-memberships-turn-one-time-participants-into-lifelong-champions) | Explicit focus on converting one-time participants into recurring members and matching membership value to engagement |
| [Campaign segmentation guide](https://university.sweatpals.com/campaigns-smart-segmentation-strategy) | Existing audience selection based on waitlist interest, attendance, location, event type and membership status; different messaging for members and non-members |
| [Host analytics guide](https://university.sweatpals.com/insights-and-reports-how-top-hosts-use-metrics-to-double-their-revenue) | Host-facing reporting includes revenue, participation, engagement, retention and campaign outcomes |
| [Gym/studio product announcement](https://sweatblog.inblog.io/121881) | Member dashboard provides membership status, visit history and billing details; check-in tracks attendance; analytics tracks participation |

The supplied investor post supplies a community-growth thesis. Its fundraising and performance claims were not independently verified here and are not prerequisites for the prototype.

## Where the proposed tool sits

Event signup -> attendance/check-in -> non-member attendee history -> membership opportunity shortlist -> host reviews suggested plan and invitation -> existing campaign system -> measure signup and subsequent retention.

The lab is a proposed decision-support component between host analytics and targeted campaigns. It does not replace existing segmentation or claim Sweatpals lacks equivalent internal models. The supplied role description already names HostCopilot, so the demo should be presented as an evaluated component that could complement that surface.

## Proposed focused prototype

- One fictional host, a few membership plans and a small fictional attendee-history dataset.
- Read-only shortlist using structured signals: repeat attendance, recency, attended activity, membership status and recent outreach.
- Exclude existing paid members, wrong-host records, people marked opted out and people inside a stated outreach cooldown. Missing consent or conflicting plan terms require host review. These are demo acceptance rules, not claims about Sweatpals policies.
- Use MiniLM/FAISS to compare voluntarily stated interests or attended-event descriptions with plan-benefit text. Similarity is relevance, not intent to buy or a conversion probability. Structured plan entitlements govern benefit claims.
- Compare an explicit attendance/recency baseline with the relevance-assisted shortlist. Explain scores and provenance. Do not infer income, health status or personal motivation.
- Show why a plan may fit. Any potential saving must be a conditional calculation based on the stated attendance pattern and plan terms, not a promise of future savings.
- Qwen may draft an invitation using only verified plan benefits and the visible evidence. Host review is required; no live emails, SMS, purchases or subscriptions.
- Preserve original policy references and expose missing dependencies, applying lessons from the AWRI evaluation.

## Evaluation and business limits

Use manually authored synthetic relevance labels to demonstrate ranking metrics such as precision@k or NDCG, and separate tests for exclusions, wrong-host leakage, incorrect benefit claims and missing information. Keep evaluation labels out of candidate inputs; do not tune on reserved final cases. Small synthetic labels demonstrate mechanics, not real conversion accuracy.

The business hypothesis is that more relevant invitations improve incremental paid signups and retained membership value with less unwanted outreach. Test it against existing segmentation using randomised eligible attendees, a comparable contact budget and an appropriate holdout. Measure incremental paid conversion, recurring revenue and subsequent retention; monitor unsubscribes and complaints. Account for people who would have joined without an invitation. High propensity is not the same as incremental benefit from outreach.

## Integration and project positioning

Start with a fictional CSV or JSON dataset and a read-only API. Real integration would require an approved event/attendance/member/plan data contract, current benefit terms, outreach permissions, outcome tracking and access controls. The public site does not establish an available integration API.

Reuse the existing FastAPI and local-model foundation. Keep the wine project intact. The honest portfolio claim is an evaluated membership-opportunity prototype, not a deployed Sweatpals feature or a trained conversion model. Validate the revised workflow before implementing the new app.
