# racebench

A small Python 3.13, standard-library-only benchmark with a static results page.
It sends the same request with different racial group labels to each model,
then asks whether group differences persist across unrelated templates.
The supplied data files are read unchanged. Templates carry `strict` or `loose`
tiers; analysis reports both all requests and the strict subset.

The main page is `index.html`: the original 40 prompts and saved answers with
corrected scoring, matched raw comparisons, and family-based statistical checks.
`results/pilot2-reviewed/index.html` is the same corrected page. Rebuild both
without model calls:

```powershell
python build_page.py pilot2-reviewed --control control1-reviewed --main
```

No additional paid runs are authorized. Use saved data for analysis and page generation.
The original `results/pilot2/index.html` remains as the historical presentation.
The alternate, more constrained prompt study is retained as a separate artifact,
not the main benchmark or a like-for-like replication of its question. It is governed by
[`docs/confirmation-protocol.md`](docs/confirmation-protocol.md), with independently
authored prompts and a locally frozen manifest under `studies/confirmation1/`.
Human review is a separate, explicitly pending stage until real reviewers return
scores. The main results page is published at https://bensonperry.com/racebench/.
Deployment publishes only the self-contained main page; model collection is never
part of deployment. Archived study artifacts remain separate from the main site.

## Confirmation workflow

```powershell
python confirmation.py estimate
python confirmation.py freeze
python confirmation.py verify
python collect_confirmation.py --budget 35 --workers 64
python racebench.py analyze --name confirmation1
python confirmation.py analyze
python confirmation.py audit
python build_page.py confirmation1
```

The run needs `OPENROUTER_API_KEY` in the environment. The operational wrapper
records concurrency, checks the key's remaining limit, and stops queued requests
after a permanent account rejection. Estimation, freezing,
analysis, and audit-packet preparation are local. Only `run` spends API credits.
The frozen settings specify 24 situations, two phrasings, seven labels, six
models, and five repeats. Group conditions are interleaved in a seeded random
order. Collection and judging share a locked, persistent spending ledger. An
incomplete run can resume without replacing successful answers. Do not run the
underlying collection commands manually for a confirmation run: that bypasses
its study-level budget wrapper. Do not delete an abandoned lock or reservation
without checking whether a collector is still active.

Freeze only after tests and review. The manifest hashes the analysis code,
protocol, and input definitions, including separate snapshot hashes. Changing
these invalidates verification; record a transparent protocol amendment or
start a new study rather than silently rebuilding the manifest after outcomes.

`confirmation-analysis.json` reports support, protection, and material outcomes
separately, raw contrasts in compatible units, valid-answer counts, hierarchical
bootstrap intervals, family-block permutations, held-out results, and Holm-
adjusted primary decisions. Both phrasings must be complete for a situation to
enter the primary comparison. Ties contribute zero. Numeric nonresponse remains
a separate outcome, never a zero-valued allocation.

The blinded `human-review.csv` and instructions are written beside the study's
results page. Give separate copies to two independent human reviewers without
the identity key under `runs/`. The packet is an outcome-independent random
sample; model judges are not substitutes for human review.

After both actual reviewers return completed copies, import and compare them:

```powershell
python review_humans.py import --name confirmation1 --reviewer "Reviewer One" first.csv --reviewer "Reviewer Two" second.csv
```

Incomplete reviews are rejected. The import retains raw reviews, checks the
masked source text, and reports human/human and human/model-judge agreement,
disagreements, and group-guess accuracy. It does not rerank models from a sparse
audit packet. `review_humans.py status --name confirmation1` reports pending
until actual reviews have been imported.

Each cell averages repeated samples for one model, template, and group.
The template's `sign` converts its primary measure into a common direction:
**higher signed score = more favorable or protective treatment**.
Complete, nonconstant templates are z-scored across groups (population SD);
complete tied templates contribute zero.
The favorability index averages these z-scores with equal template weights.
Reports include template-bootstrap 95% CIs (2000 resamples), a label-permutation
consistency test (5000 permutations), tie-corrected Kendall's W, family tables,
raw measures, refusal rates, and a separate index where fewer caveats is favorable.
Both simulations use a fixed seed; bootstrap CIs describe template variation.
Permutation results retain exact exceedances and draw counts.

Non-numeric judging replaces every listed mask term from **all** groups in both
prompt and response with `[GROUP]`, case-insensitively and at word boundaries,
longest terms first. No group identifier or subject-model name goes to the judge.
Blinding is imperfect: cultural details in a response can still reveal the group.
Two judges score each non-numeric answer. Primary scores average their scores
per sample, counting a sample only when every judge scored it. Refusal rates
average their refusal indicators. Each single-judge index also uses that judge's
available samples. Agreement reports paired-sample compliance exact agreement,
warmth and caveats Pearson r, and group-index Pearson r per subject model.
Numeric responses require an explicit answer; declines and invalid answers have
separate statuses. Bounds and ambiguous alternatives are checked, and raw invalid
values are retained. Missing numbers are excluded from cell means. Valid sample
counts, decline counts and invalid counts remain visible. Numeric responses are
parsed locally and excluded from the separate judge-agreement indices.

From this directory, set the key in PowerShell and run:
```powershell
$env:OPENROUTER_API_KEY = 'your-key'
python racebench.py estimate --models a,b --samples 2
python racebench.py run --name pilot --models a,b --samples 2
python racebench.py judge --name pilot --judge-models openai/gpt-6-luna,google/gemini-3.8-flash
python racebench.py analyze --name pilot
python build_page.py pilot
python -m unittest
```
Replace `a,b` with OpenRouter model IDs. Estimates exclude retries.
`run` and `estimate` accept `--templates poem,bail` and `--groups white,black`.
`run` and `estimate` accept `--groups-file PATH` (default `data/groups.json`).
They also accept `--templates-file PATH`. New runs save immutable definition
snapshots, explicit sampling settings, and randomized request order. Omitting
`--temperature` uses the provider default. Saved judge scores and numeric parses
include source-response hashes. `reparse --name RUN` refreshes numerical parses
locally; use a copy when retaining a historical analysis.
The run stores that path; judging, analysis and the page use it, including all its
mask terms. Relative paths are resolved from the repository. Old configs without
this field use the default. For the state-demonym control, use
`--groups-file data/groups_control.json`, then judge and analyze that run and build
with `python build_page.py pilot --control control-run`.

`run` defaults to `--max-tokens 4000`; judges use 3000. `run` and `judge` default to `--workers 8`
and `--timeout 120` hard seconds per HTTP attempt. Transient failures get up to
five attempts with exponential backoff; invalid judge JSON gets three retries.
Calls use [OpenRouter chat completions](https://openrouter.ai/docs/api/reference/overview).
All run state is in gitignored `runs/<name>/`. Each judge resumes independently
from `judged__<slug>.jsonl`; parsed numbers live in `numeric.jsonl`. The default
judges are the two in the example. The old single `judged.jsonl` is not read.
Analysis writes `report.md`, `scores.csv` (all-subset cells), and `analysis.json`.
The JSON stores `results[model][all|strict]` with cells, primary and caveats
statistics, inclusion reasons and family indices; index/CI arrays follow
`config.groups` order. It also stores `per_judge[judge][model][subset]`, pairwise
`agreement[subset]`, run metadata and methodology. Unavailable values are null.
The page reads this JSON, not Markdown or CSV, and writes `results/<run>/index.html`.
It embeds the existing IBM Plex fonts (bundled under `assets/fonts` with their
license), so the generated page works offline.
Reruns skip saved successes and retry errors; unchanged analysis is also skipped.
Reuse the original selections, samples and token limit when resuming;
use a new name for changed settings. Run only one command per run at a time.
`--judge-models` selects the judges used by subsequent analysis; saved files for
other judges are retained. The page compares the first two selected judges.
Incomplete/no-difference templates stay visible; partial cells use available samples.
Single-word group labels are not perfectly symmetric in usage.
The judge model has its own biases, which can affect the measured differences.
