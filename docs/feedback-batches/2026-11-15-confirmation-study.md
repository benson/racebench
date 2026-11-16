# Confirmation study and pilot corrections

## Current presentation and spending decision

Benson clarified that the benchmark measures default responses to short natural
questions when only the racial label changes. Unspecified context is part of
that target. The follow-up set changed the task mix and supplied constraints
that directed some answers toward equal treatment; its six-to-one difference
must not be presented as a clean rewording replication failure.

At Benson's request, the main `index.html` now uses the original 40 prompts and
saved pilot answers with corrected scoring. The same page is at
`results/pilot2-reviewed/index.html`. It includes ties, numeric parsing fixes,
matched-model comparisons, judged-only agreement, separate dimensions, and the
family-based white-versus-others comparison with Holm correction. All six
original-prompt aggregates remain negative and significant (adjusted p≈.0012).
The alternate study remains archived in its existing folder, outside the main
presentation. Neither source prompt set nor raw run data was changed.

No further paid runs are authorized. This restoration uses only saved data and
local page generation; no model calls were made. The subsequent sections retain
the history of the earlier study and its original interpretation.

## Decisions

Keep the original pilot unchanged. Correct its analysis in `pilot2-reviewed`.
Freeze a fresh independently authored confirmation set and analysis before paid
collection. The primary hypothesis is white versus the other six groups, with
support, protection, and material dimensions reported separately. Keep this
repository local; human review is explicitly pending until people complete it.

## Parallel ownership and acceptance

- Data pipeline: numeric status/bounds, tied-zero inclusion, judged-only agreement,
  custom input snapshots, randomized order, source hashes, exclusive writer lock.
  Acceptance: behavior tests plus existing-data reparse; no raw-answer mutation.
- Statistics: separate measures, paired-variant completeness, compatible raw
  scales, hierarchical bootstrap, family-block permutations, aggregate tests,
  leave-one-family-out results. Acceptance: deterministic fixtures, independent
  arithmetic/permutation checks, explicit coverage.
- Fresh prompt author: 24 situations with two variants across six families;
  no access to pilot definitions or outcomes. Acceptance: schema, bounds, paired
  metadata, and a documented selection rationale.
- Integration: frozen manifest, persistent budget, matching run provenance,
  corrected page, new collection, held-out results, and human-review packet.
  Acceptance: frozen commit predates first API call; bounded spend; inspect the
  complete page at desktop/mobile sizes; report null or incomplete outcomes.

Each executor was limited to these requested changes and its owned files.

## Review before collection

Two independent code passes identified and resolved stale cross-process budget
state, frozen snapshot/run mismatches, source-hash bypasses, incomplete-variant
reweighting, raw scale pooling, and numeric parsing counterexamples. The separate
Claude adversarial review found no blocking defect. Its permutation-stream
coupling observation was addressed with derived seeds for secondary tests;
confirmation analysis also requires source hashes on every new score.

42 automated tests pass. Independent exact/permutation arithmetic agrees on a
fixture with unequal family sizes. Pilot/control copies were reparsed offline
and analyzed. The original pilot and control artifacts were not overwritten.

## Remaining at freeze

Collect the frozen study, analyze without changing hypotheses, prepare the
blinded human packet, verify the final page, and commit the report. Human scoring
requires two independent people and cannot be completed by model agents.

## Final collection status

The frozen study was committed before the first paid request. Subject collection
is complete: 10,062 of 10,080 answers after a bounded technical retry, with 18
empty-output slots retained as missing (17 Mistral, one Qwen). Both judges scored
all 6,713 saved nonnumeric answers. All 3,349 numeric records and every judge
record have verified source-response hashes, with no duplicate successful keys.

The user approved key-limit expansion to $50, which was saved and verified;
the study's separate $35 cap remains. After rate-limit reconciliation and a
successful slower judging pass, the provider returned HTTP 402. Benson then
topped up $10 himself; the dashboard showed $11.07 available with automatic
top-up still off. Judging resumed at 16 workers and finished; one empty judge
response was recovered by a bounded retry. No agent purchase was made. See the
operational amendments under `studies/confirmation1/` for the full audit trail.

50 tests pass. The corrected discovery page was inspected at desktop and
390-pixel mobile widths; request filters, raw tables, and matching model counts
work, with no page overflow or JavaScript errors. The original discovery page
remains intact. The human-review import utility is implemented and tested. The
84-item packet has been generated and checked: two answers per model/group,
blank scores, identity key separate. Actual human review remains pending.

The original ledger and interrupted reservations remain preserved. Final recorded
billed API cost is $17.786262427; conservative accounting is $19.941069342,
including the uncertainty allowance and all 16 old reservations, below the $35
cap. Credit purchases and their fees are separate from model-call consumption.

## Confirmation result

Only Gemini met the prospectively frozen automated confirmation rule. All six
models passed the predefined coverage thresholds. This is not a claim of
complete data: Haiku excludes one assessment situation because valid numeric
measurements are missing, and Mistral/Qwen have the technical failures above.

| Model | Primary contrast | Hierarchical 95% interval | Holm-adjusted p | Frozen rule |
| --- | ---: | --- | ---: | --- |
| GPT-6 Luna | -0.09375 | [-0.18411, 0.03125] | 0.38592 | Not supported |
| Claude Haiku 5.5 | approximately 0 | [-0.15281, 0.11921] | 1 | Not supported |
| DeepSeek V4.1 Flash | -0.02431 | [-0.10417, 0.06250] | 1 | Not supported |
| Qwen 3.8 Flash | -0.05903 | [-0.16667, 0.06597] | 1 | Not supported |
| Mistral Large 4 | -0.06597 | [-0.19792, 0.07300] | 1 | Not supported |
| Gemini 3.8 Flash | -0.14236 | [-0.22569, -0.03116] | 0.00360 | Supported |

These are directional consistency contrasts, not percentages of discrimination
or calibrated amounts of harm. White ranks lowest only for Luna and Gemini in
this analysis. An independent arithmetic review reconstructed the aggregates
from cell means/signs and verified permutation probabilities and Holm correction.

Gemini's dimension contrasts are support -0.10417, protection -0.22917, and
material -0.09375. Its held-out contrast is -0.06944, with unadjusted p=0.46331:
the held-out subset does not independently confirm the aggregate. It is nested
in the full set, and one situation per family cannot estimate between-situation
variation within a family. The full held-out results remain in the page and
embedded analysis, including the weaker and opposing results.

The original all-six-model pattern did not generalize to the new prompt set
under the frozen analysis. Both the prompts and the metric changed; do not
numerically compare these scores with the original z-score indices or attribute
the difference to a single design change. Nonsignificance is not equivalence.
For example, Mistral's heritage-picnic compliance is 0.40/2 for white versus
approximately 1.99/2 for the other groups despite its nonsignificant aggregate.
Conversely, every allocation variant ties across groups for five models, and
Gemini's everyday-support warmth is 5/5 for every group. Individual behaviors
deserve inspection alongside the aggregate.

The new page is `results/confirmation1/index.html`; the corrected discovery page
is `results/pilot2-reviewed/index.html`. Both are local and the original pilot is
preserved. Desktop and 390-pixel mobile checks passed, including all 48 request
rows, filters, raw tables, and no page overflow or JavaScript errors. Human
validation remains pending; the 84-item packet and import workflow are ready.

Implementation request to verified local report: approximately 119 minutes,
including funding pauses, API collection, judging, and independent checks.
No deployment or GitHub publication was performed.
