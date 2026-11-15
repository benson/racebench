# swapbench

A small Python 3.13, standard-library-only benchmark with no web UI.
It sends the same request with different racial group labels to each model,
then asks whether group differences persist across unrelated templates.
The supplied `data/templates.json` and `data/groups.json` are read unchanged.

Each cell averages repeated samples for one model, template, and group.
The template's `sign` converts its primary measure into a common direction:
**higher signed score = more favorable or protective treatment**.
Complete, nonconstant templates are z-scored across groups (population SD).
The favorability index averages these z-scores with equal template weights.
Reports include template-bootstrap 95% CIs (2000 resamples), a label-permutation
consistency test (5000 permutations), tie-corrected Kendall's W, family tables,
raw measures, refusal rates, and a separate index where fewer caveats is favorable.
Both simulations use a fixed seed; bootstrap CIs describe template variation.

Non-numeric judging replaces every listed mask term from **all** groups in both
prompt and response with `[GROUP]`, case-insensitively and at word boundaries,
longest terms first. No group identifier or subject-model name goes to the judge.
Blinding is imperfect: cultural details in a response can still reveal the group.
Numeric responses use their first number; no number means a numeric refusal.
Missing numbers are excluded from cell means, but included in refusal rates.

From this directory, set the key in PowerShell and run:
```powershell
$env:OPENROUTER_API_KEY = 'your-key'
python swapbench.py estimate --models a,b --samples 2
python swapbench.py run --name pilot --models a,b --samples 2
python swapbench.py judge --name pilot --judge-model openai/gpt-6-luna
python swapbench.py analyze --name pilot
python -m unittest
```
Replace `a,b` with OpenRouter model IDs. Estimates exclude retries.
`run` and `estimate` accept `--templates poem,bail` and `--groups white,black`.
`run` defaults to `--max-tokens 700`; `run` and `judge` default to `--workers 8`
and `--timeout 120` hard seconds per HTTP attempt. Transient failures get up to
five attempts with exponential backoff; invalid judge JSON gets three retries.
Calls use [OpenRouter chat completions](https://openrouter.ai/docs/api/reference/overview).
All run state is in gitignored `runs/<name>/`, including `report.md` and `scores.csv`.
Reruns skip saved successes and retry errors; unchanged analysis is also skipped.
Reuse the original selections, samples, token limit, and judge model when resuming;
use a new name for changed settings. Run only one command per run at a time.
Incomplete/no-difference templates stay visible; partial cells use available samples.
Single-word group labels are not perfectly symmetric in usage.
The judge model has its own biases, which can affect the measured differences.
