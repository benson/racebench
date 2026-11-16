# Judge throttling and aggregate billing reconciliation

The first judge scored all 6,713 saved nonnumeric answers successfully. The
second judge scored 929 before provider rate limiting and conservative retry
reservations exhausted local budget headroom. There were 256 final HTTP 429
errors; 5,528 remaining jobs were stopped without sending a request. These are
technical missingness, not model judgments. No study outcomes were analyzed.

Collection had ended before billing was inspected. The authenticated key's
cumulative usage was $20.190610176 at the earlier collection resumption. Idle
observations on 2026-11-16 UTC were:

- 03:08:52: $30.839802478, initially below locally reported costs.
- 03:10:04: $30.869093728.
- 03:11:18: $30.869093728, unchanged.

The counter demonstrably lagged, so the first observation was not used to
reduce accounting. After stabilization, settled accounting was reconciled to
the prior reconciled balance ($1.280538415), plus the greater of the cumulative
key-usage increase ($10.678483552) and post-resumption reported costs
($10.676506752), plus an explicit $1 uncertainty cushion. All 16 earlier
interrupted reservations ($0.703087275) remain untouched. The resulting
conservative total was $13.662109242. Any unrelated use of this key is included
in the usage increase and therefore makes this reconciliation more conservative.

This is aggregate billing reconciliation, not proof that each individual retry
was free. The cushion is a buffer, not a demonstrated bound on late charges.
The key's $50 lifetime limit also remains in place. Original ledger entries,
source hash, baseline, observations, calculations, and the uniquely identified
append-only correction are preserved under the run directory. An independent
review checked the arithmetic and the reported-cost floor before application.

Judging resumed at 16 concurrent requests, retaining all successful scores.
The study's $35 accounting cap, frozen inputs, source hashes, scoring rubric,
and hypotheses are unchanged. The subject collection stage was not repeated.
