# Operational amendment: collection concurrency

Recorded after 411 subject slots had returned, before examining answer contents,
group effects, or scores. The original 16-worker collection pace implied several
hours. Subsequent collection uses up to 64 workers through
`collect_confirmation.py`, whose only argument override is the worker count
passed to the original collector and judge. Original source hashes, frozen
manifest, prompt definitions, sample size, randomized job list, API payloads,
scoring, stopping criteria, and $35 accounted-cost cap are unchanged.

The first collector was interrupted. Its unfinished spending reservations remain
charged conservatively in the persistent ledger. Abandoned locks were removed
only after confirming their owning process and request subprocesses had exited.
Successfully saved answers are retained. Missing or errored slots resume through
the existing success-key mechanism, without selecting on answer content.

Concurrency changes can affect provider queuing/routing and timing. Collection
records retain the requested worker count and timestamp; this amendment is an
operational limitation, not a claim of identical execution timing. No outcomes
were used to choose the change.
