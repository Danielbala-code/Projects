# Build decisions and final review

- Reused the existing cloud checkout and implemented inline. The user's instruction to finish authorised proceeding through implementation and publication without another planning approval round.
- Mounted `/membership/` in the existing FastAPI process and shared Qwen. This avoids duplicating a multi-GB model instance on a small Codespace; both routes were tested together.
- Kept synthetic labels out of ranking and prompts. Did not change labels or weights to create an embedding advantage. Keyword ranking remains the default because this fixture showed equal measured relevance with less latency.
- Reproduced and corrected the harmless “feel free to” validation false alarm. Other “free” benefit claims remain blocked. The checker is not complete semantic verification.
- One fresh whole-branch reviewer found one Important defect: the tokenizer artifact's embedded padding/truncation conflicted with custom masking. Two failing regressions demonstrated the issue, the encoder was corrected, and the actual benchmark was rerun. The suite passed 35 tests and 8 subtests after this correction. No Critical findings or deferred minors were reported.
- The reviewer declined to assess production tenant/authentication controls, complete semantic certification, causal business lift and live deployment readiness. Those are outside this fixed fictional demo. Their absence is disclosed in the README and evaluation; they remain prerequisites for production use.
- Publish only a non-force fast-forward to the user's existing public repository. Code publication does not restart the user's separate Codespace; the README includes its exact update/start commands.

Reusable cloud setup and startup instructions were saved as an environment configuration draft. Saving the draft does not publish an environment snapshot or migrate the user's existing Codespace.
