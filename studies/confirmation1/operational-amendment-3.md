# Authorized account limit and conservative reconciliation

On 2026-11-16 UTC, Benson explicitly approved raising the existing OpenRouter
key's lifetime limit from $20 to $50 and finishing the study. The saved dashboard
showed $20.19 used and $29.81 remaining. The study's separate $35 cap is unchanged.
No credits were purchased and no recurring limit was introduced.

Before resuming, the prior ledger and response-file hashes were checked against
the prepared reconciliation proposal. There were 4,209 HTTP 403 quota rejections
after the exhausted key was observed. For each model, the corresponding number
of cheapest unknown settlements was credited, totaling $31.714856465. This is a
conservative aggregate reconciliation: the original ledger did not map settlement
IDs directly to response IDs, so exact rejected-call matching is unavailable.
The proposal, applied record, original events, and credited settlement IDs remain
in the run directory. No prior event or response was deleted or rewritten.

Unmatched unknown settlements and all 16 interrupted reservations remain charged.
The reconciled accounted amount, including those reservations, was $1.9836.
Collection resumed at 64 concurrent requests with the account-error guard.
Prompts, hypotheses, source hashes, judging, and analysis remain frozen. No new
outcome analysis was performed before resumption.
