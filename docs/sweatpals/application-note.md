# Application material — Sweatpals

Use the project as evidence of your approach. Add your own employment history, education and results separately; this prototype does not establish years of professional experience or production ML ownership.

## Portfolio description

Built Membership Opportunity Lab, a host-facing prototype inspired by Sweatpals' public membership and campaign workflows. It identifies eligible repeat attendees, explains membership-plan fit and prepares source-grounded invitations for human review. The implementation combines FastAPI, transparent eligibility rules, a keyword baseline, quantized MiniLM embeddings with FAISS, and local Qwen inference. I measured the baseline against the embedding approach and kept the baseline as default because the small synthetic evaluation showed equal relevance with lower latency.

Repository: https://github.com/Danielbala-code/Projects/tree/main/docs/sweatpals

## Why this problem

Sweatpals connects offline attendance with community and recurring host revenue. Its public guides already describe memberships and attendance-based campaigns. I focused on the decision between those features: which eligible attendees might find a particular plan useful, what evidence supports that suggestion, and how to prepare an accurate invitation. This could complement a host assistant rather than duplicate basic audience segmentation.

## What I would validate next

The business hypothesis is more incremental paid signups and retained membership value with less unwanted outreach. I would first agree a host-scoped data contract and audit attendance, membership, benefit and consent freshness. Then I would compare against the existing campaign baseline using a randomised eligible audience, equal contact budgets and a no-contact control. Metrics would include incremental paid conversion, recurring revenue, later retention, unsubscribes and complaints. High likelihood of joining does not imply that an invitation caused the signup.

## A concise interview explanation

“I reused an existing local-model application to build a membership-opportunity component. I researched the public product first and found that memberships and segmentation already existed, so I narrowed the contribution to transparent recommendations and grounded drafting. Consent and plan terms are deterministic; embeddings only compare stated interests with benefits. The prototype uses fictional data. Both ranking modes scored the same on the synthetic fixture, so I chose the faster baseline as default. I also recorded a rejected real-model draft rather than treating schema-valid JSON as correct. The next step would be real labels and an incremental-conversion experiment.”

## Before submitting

- Link this project README and its evaluation, not only the repository root.
- Confirm the public Codespace's `/membership/` route opens in a private browser window, or use the screenshot and reproducible instructions if it is asleep.
- Replace any personal-history placeholders in your actual application with your own facts. Do not describe this as deployed at Sweatpals, real customer revenue impact, a trained conversion model, or an official integration.
