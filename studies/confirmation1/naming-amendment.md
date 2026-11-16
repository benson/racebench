# Project renamed to Racebench

On November 16, 2026, Benson renamed the project from Swapbench to Racebench
and requested publication of the corrected original-prompt results.

The main module and its tests were renamed to `racebench.py` and
`test_racebench.py`; imports, report headings, page branding, and current
documentation follow the new name. Scoring, prompts, saved answers, and
statistical results were not changed. No model calls were made.

The frozen manifest is deliberately unchanged. Its source names and hashes
refer to the pre-rename code, available in commit
`23a20b5`. Verification against the renamed working tree reports a source
change rather than certifying it as the original frozen code. Missing frozen
source paths are reported as changes, not unhandled file errors. Do not
re-freeze this completed study to hide the naming change.

Deployment publishes only the current self-contained main page. The alternate
study remains an archived experiment and is not incorporated into its results.
