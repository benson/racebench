# Confirmation study and pilot corrections

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

## Current collection status

The frozen study was committed before the first paid request. Collection saved
989 of 10,080 subject slots, then stopped when the provider key's existing $20
lifetime limit was exhausted. No new outcomes have been analyzed or judged.
The user approved key-limit expansion to $50, which was saved and verified;
the study's separate $35 cap remains. See the operational amendments under
`studies/confirmation1/` for concurrency, interruption, and account-error handling.
Collection has resumed after conservative ledger reconciliation.

49 tests pass. The corrected discovery page was inspected at desktop and
390-pixel mobile widths; request filters, raw tables, and matching model counts
work, with no page overflow or JavaScript errors. The original discovery page
remains intact. The human-review import utility is implemented and tested, but
the actual human packet awaits completion of collection and judging.

The reconciliation retains unknown/interrupted reservations and the original
ledger. Finish source collection, judging, confirmation and held-out
analysis, human-packet generation, page QA, and the final results commit. Do not
label the partial run a confirmation or a null result.
