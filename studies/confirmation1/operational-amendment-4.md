# Scoring after bounded technical retries

The first complete subject pass saved 10,002 of 10,080 planned responses.
A second pass retried only the 78 failed slots and recovered 60, leaving 18
empty-output failures. All successful answers, including refusals, were retained.
No outcome scores or group comparisons were inspected when choosing to stop
subject retries. Coverage is 99.82%; model-specific missingness will be reported.

The operational wrapper gained `--judge-only` so that persistent subject errors
do not prevent scoring saved answers. This skips only the subject collection
stage inside the existing frozen execution path. Manifest verification, run
binding, study lock, current-price reservation, the shared $35 ledger, account
headroom check, and account-error stop remain active. Missing answers are not
filled or treated as refusals, and successful responses are not replaced.
The frozen analysis and its coverage requirements remain unchanged.

This operational change was tested before use. It does not alter the scoring
rubric, judge endpoints, source hashes, sampling, or hypotheses.
