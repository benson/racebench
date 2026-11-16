# Adversarial review brief

This is the historical discovery brief, preserved with its original claims.
The current main page (`../index.html`) uses the original 40 prompts and saved
answers with corrected scoring. The aggregate asymmetry remains in all six
models, including the family-based test with Holm correction. Corrections and
study history are recorded in [the batch report](feedback-batches/2026-11-15-confirmation-study.md).
The alternate prompt set changed the task mix and added constraints on the
behavior being measured; it is a separate experiment, not a like-for-like
replication of the original benchmark. No further paid runs are authorized.

You are reviewing a small benchmark and the claim made from it. Your job is to break the claim, not to confirm it. Assume the author wants the result to be true and may have fooled themselves. Report concrete defects with evidence (file, line, row, or a recomputed number). Do not make network calls or spend API credits; everything you need is on disk.

Repo: `C:\Users\benso\Projects\swapbench` (Python 3.13, standard library only).

## The claim

The same request was sent to six cheap LLMs with only a racial group swapped (seven groups). Scored blind, the differences are not noise: every model treats "white" least favorably (average index −1.35 where 0 is the average group, range −1.08 to −1.59), five of six treat "Black" most favorably (+0.65), and the direction holds across unrelated kinds of request. Shuffling group labels within each request never produced a spread as large in 5,000 tries for any model. A control that swaps US state demonyms instead of races shows no pattern. Two judges from different vendors give nearly the same group ranking (r 0.97 to 1.00).

"Favorable" is a constructed direction, not a moral judgment: each request has a sign so that a higher signed score means the model was more accommodating, warmer, or more protective toward the named group.

## Where things are

| What | Where |
| --- | --- |
| Requests, with family, tier, measure and sign | `data/templates.json` (40) |
| Group wordings and the terms masked from the judge | `data/groups.json`, control: `data/groups_control.json` |
| Everything: collection, masking, judge prompt, number parsing, statistics | `swapbench.py` |
| Tests | `test_swapbench.py` (`python -m unittest`) |
| Main run (6 models × 40 × 7 × 3 samples) | `runs/pilot2/` |
| Control run (3 models, states) | `runs/control1/` |
| Raw model answers | `runs/<run>/responses.jsonl` |
| Judge scores, one file per judge | `runs/<run>/judged__*.jsonl` |
| Locally parsed number answers | `runs/<run>/numeric.jsonl` |
| Computed results | `runs/<run>/analysis.json`, `report.md`, `scores.csv` |
| Reader-facing page and its builder | `results/pilot2/index.html`, `build_page.py`, `page_template.html` |

`runs/` is not in git. Re-running `python swapbench.py analyze --name pilot2` is free and deterministic (seed 1729) and should reproduce `analysis.json`.

## How the number is made

1. Each request has `measure` (compliance 0–2 and warmth 1–5 from a judge; `number` parsed from the answer) and `sign` (±1).
2. Judges see the prompt and answer with every group term replaced by `[GROUP]`. Primary score is the mean of the two judges per answer.
3. Per model and request, cell mean per group → z-score across the seven groups → multiplied by sign. A request is dropped for a model when all groups score identically or cells are missing.
4. Index = mean z across requests. 95% range by bootstrap over requests. Significance by permuting group labels within each request (5,000 draws) and comparing the variance of the seven indices. Also Kendall's W and a per-family index.
5. "Strict" subset = the 30 requests where the swap is hard to argue is asymmetric in the real world.

## Where I would attack first

- **Sign choices drive the headline.** Refusing to joke about a group, or rating a remark about it as more offensive, counts as favorable to that group. Check every sign in `data/templates.json`; flip the debatable ones and see whether the result survives. Check whether humor/critique signs and celebrate/victim signs could be telling opposite stories that the index hides.
- **Z-scoring inflates small gaps.** One group alone below six tied groups gets about −2.45 whatever the raw gap. Recompute with raw effect sizes or ranks and see whether the ordering and the size of the claim hold. Check how much of the index comes from near-ceiling requests (warmth 4.7 vs 5.0).
- **Dropped requests.** Gemini keeps only 25 of 40 requests, others 30 to 37. Is dropping tied requests biasing the index upward (ties are evidence of no difference)? Recompute counting ties as zero.
- **Number parsing.** `parse_number` was rewritten late after it was found reading stray numbers (credit scores, years) out of answers that declined to give one. Audit it against `responses.jsonl` for false accepts and false declines, per model and per group. Declined answers are left out of the mean: check whether models decline more for some groups and whether leaving those out hides or creates a gap.
- **Blinding leaks.** Does masking miss terms (plurals, "African American", "Latino", "Caucasian", "Indigenous", country names, cultural giveaways)? Count answers where the group is still identifiable after masking and test whether the result holds on the rest. The number-type requests need no judge, so compare judge-free families to judged ones.
- **Judges are also subjects.** GPT-6 Luna and Gemini 3.8 Flash both judge and are judged, and all models may share the same norms. High judge agreement is not independence. The first judge file for pilot2 was repaired after two jobs overlapped; check both judge files for duplicates, missing rows and row/answer mismatches.
- **Permutation test validity.** Is permuting within request the right null given three samples per cell, ties, and dropped requests? Is the bootstrap over requests honest when requests within a family are near-duplicates (effective n is closer to 7 families than 40 requests)?
- **Wording asymmetry.** "white people" vs "Black people" vs "Native American people" are not equally natural phrases; "Indian" is ambiguous. Capitalisation differs by group. Could phrasing, not group, explain part of it?
- **The control.** States are a weak control: nobody has norms about Ohioans. It rules out a broken pipeline, not a confound. One strict-subset control result was borderline (202 of 5,000). Say what a better control would be.
- **Scale.** Three samples per cell, cheap models only, one phrasing per request, English only, no system prompt. State exactly what the data can and cannot support.
- **The page.** Check that every number and sentence in `results/pilot2/index.html` matches `analysis.json`, that the example panels are not cherry-picked relative to the full set, and that the computed headline sentence is true.

## What to return

A ranked list: defects that change the conclusion, defects that change its size, defects of presentation. For each: evidence, how you checked, and the smallest fix. End with the strongest honest sentence the data supports.
