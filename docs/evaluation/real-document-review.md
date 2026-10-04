# Real-document evaluation: AWRI TN05

An interview portfolio evaluation of the public AWRI procedure for rescue of stuck or slow alcoholic fermentation. [Original document](https://www.awri.com.au/wp-content/uploads/TN05.pdf). This is independent testing of our prototype, not AWRI or Vinarchy endorsement. The PDF and the user's uploaded export are not distributed in this repository.

## Method

First assessed the exported SKILL.md on its own, without reopening the source during that assessment. This was not fully blind: the evaluator had previously read portions of the source while finding a suitable test PDF. Then compared the user's original PDF and complete exported ZIP. Checked source quotations, page text preservation, dependencies, review metadata and generic quality-check warnings. Also inspected the application pipeline to explain the observed failures. This is one real-document case, not a general accuracy benchmark.

## What worked

- All nine quoted source passages matched their cited PDF pages after whitespace normalization.
- All five pages' extracted text were preserved in references/source.md, matching extracted PDF text after whitespace normalization. This does not establish visual or table-layout fidelity.
- The recorded source fingerprint matched the uploaded PDF.
- Export metadata recorded local-model generation and acknowledgement.
- Full source references retained context omitted from the main skill.

## What failed

| Original information | Main-skill result |
|---|---|
| Applicability conditions, page 1 | When to use was replaced by the first heating action |
| Nine preliminary checks/actions, page 2 | Not represented as prerequisites |
| Reactivation-medium recipes, page 3 | Not included alongside the dependent instruction |
| Step 8 across pages 3–4 | Quote stopped halfway through a warning |
| Additions table and progression guidance, page 4 | Not represented in the main skill |
| Subsequent controls and recovery conditions, pages 4–5 | Not represented in the main skill |

Several AI clarifications omitted quantities, timing conditions, alternatives or escalation details that remained in the accompanying quotations. Metadata still referred to a reporting procedure. The original and reviewed draft objects were identical: no draft edits were recorded. Acknowledgement does not establish the quality or completeness of human review.

## Why these failures occurred

The numbered-drafting path sends individual numbered passages to the model. Other context is retained in references but is not included in that drafting path. Passages are separated page by page, so a continuation can become detached from its numbered instruction. Citation validation checks whether a quotation appears in the source, not whether it is complete. The renderer uses generic reporting metadata. A larger model alone cannot recover context absent from its input.

## Quality-check limitations

The generic checker reported 45.0, explicitly a structural score rather than business accuracy. Its code-example warning is poorly suited to this business procedure. It also flagged nine reference links even though their files and conventional Markdown heading targets existed; these appear to be false positives. Rendered links were not separately evaluated in this comparison.

## Defensible claims and next work

The prototype demonstrates source-referenced drafting, local CPU inference, editable review and portable packaging. It does not demonstrate complete procedure conversion or organisational approval.

Next work: preserve applicability and prerequisites; connect tables and cross-page continuations; check quantities, units, decision conditions and unresolved dependencies; prevent operational approval when important gaps remain; and evaluate a second unseen procedure. Review quality must be assessed separately from interface and API correctness.
