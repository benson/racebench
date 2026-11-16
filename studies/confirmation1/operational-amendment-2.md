# Operational amendment: exhausted provider key

Collection stopped with 989 successful subject responses. No judge collection
or outcome analysis was started. The authenticated OpenRouter key-status endpoint
reported a lifetime limit of $20, usage $20.129041659, and no remaining limit.
That limit covers prior work as well as this study. The study's response ledger
contains approximately $0.92 of reported costs, including unsuccessful empty
responses that returned usage. Final billing may differ from response estimates.

The original collector continued trying distinct queued slots after a permanent
account-level 403, until the separate conservative ledger approached its cap.
Those quota rejections are not model refusals or observations. They remain raw
error records and are excluded from analysis. No valid answer is discarded or
replaced. The missing slots make this an incomplete study, not a negative result.

`collect_confirmation.py` now checks account headroom before collection and stops
sending queued work after the first 401/402/403 or local-budget rejection. Already
in-flight calls can finish. This operational guard does not alter prompts, API
payloads, sample size, scoring, or frozen source hashes. Focused offline tests
exercise both exhausted-key preflight and stopping after a permanent rejection.

The spending ledger currently includes conservative reservations for rejected
requests and interrupted calls. It must be reconciled transparently against
provider billing before resuming; it must not be reset or silently replaced.
The $35 study cap remains in force. Raising the provider key's existing lifetime
limit is awaiting the user's explicit approval. No credit purchase, limit change,
or further model call has been made while that decision is pending.

Provider reference: [OpenRouter's exhausted-key handling](https://openrouter.ai/blog/ai-agent-infinite-loop/)
states that requests blocked by an exhausted key stop before model execution.
Keep unknown interrupted reservations conservative; do not infer a model outcome
from a quota error.
