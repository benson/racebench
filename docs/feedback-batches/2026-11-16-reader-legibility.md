# Reader legibility

Benson requested a finding-led title and short abstract, concrete examples,
plain-language labels, visible answers, and less vertical repetition. He chose
the compact request browser after reviewing this sketch:

1. Finding-led title and short summary.
2. The existing six examples, retaining mixed salary results and equal-scoring
   support for an excluded daughter alongside larger gaps.
3. Overall group comparison and state-label control, on the same scale.
4. Plain-language summaries of support, protection, and practical decisions;
   statistical tables and score definitions available in expandable detail.
5. A request list and one selected question: visible answers, compact group
   chart, and expandable exact numbers. On phones, use a request selector.
6. Methodology and statistical details, expandable.

## Rules

- The claim is about the aggregate of these 40 prompts, not every race-related
  question. All six models place white lowest overall; support for the daughter
  prompt is equally high across groups, and salary directions vary by model.
- Preserve prompt text, saved scores, sample counts, uncertainty, and all seven
  groups. No new collection, judging, analysis run, or API expenditure.
- Preserve the existing six examples. Do not choose model or answer samples by
  the size of the gap. Answer displays default to the first configured model and
  first saved sample; their scores average the valid repeated answers.
- Show the full saved first answer instead of the former 1,400-character export
  cutoff. Visually bounded answer areas must remain scrollable and selectable.
- Move count repetition and statistical jargon into disclosure sections; keep
  the score scale, score direction, source model, and missingness understandable.
- Keep keyboard focus visible, selection on the whole button surface, no accent
  rails, and no layout motion. Preserve the user's words in prompts and answers.
- No unrequested user-visible features or copy; additions are limited to the
  findings, explanations, disclosures, and browser requested in this brief.

## Acceptance

Verify all 40 questions are reachable, model and group selectors show matching
saved answers, filters remain accurate, and detail tables retain counts and
uncertainty. Review desktop and phone screenshots as complete surfaces. Obtain
an independent visual review for the new layout. Keep this iteration on its
branch until Benson accepts publication.

## Implemented and checked

- New title: “Six language models responded least favorably toward white people
  overall.” The abstract limits the conclusion to these 40 prompts and includes
  the equal-scoring daughter example and mixed salary results.
- Original six examples retained, with white/Black averages, first saved answer
  pairs, and counts for all seven groups behind a disclosure.
- Main charts keep their original scores and common scale. Statistical tests,
  family comparisons, and judge agreement remain accessible in disclosures.
- All 40 requests are reachable through a list on desktop or a native selector
  on narrow screens. Model/group changes were checked against saved answers.
- Full first answers restored in 534 cases; all embedded analysis data other
  than answer text is byte-equivalent as parsed data to the preceding version.
- All 51 unit tests pass. Browser checks cover every request, model/group
  changes, request-type filtering, exact values, missing numeric answers,
  example navigation, and the overall subset control. No page errors observed.
- Visual review covered desktop and 390px layouts; additional width check at
  320px found no horizontal overflow. Physical-phone testing was not available.
- Independent visual and precision reviews led to fixes for numeric scale lower
  bounds, stacked phone answer panels, the visible definition of favorable,
  directed score semantics, missing-data scope, and the protection category label.
- No API/model runs. This version is saved on a non-deploying review branch.

## Answer-range follow-up

Benson removed the eyebrow header and the introductory example paragraph. He
found changing score labels and numerical scales difficult to parse, and asked
for answer ranges plus a way to find questions with recurring differences.

Bounded measures now share a labeled range display using their original bounds;
warmth and compliance are introduced as plain questions. Dollars and months
retain their real units. Exact averages, counts, and scale definitions remain
available in details. The full embedded data is unchanged.

An optional White–Black ordering ranks questions by the number of models
favoring the same group, then their share of comparable models, preserving the
original order for ties. Counts show the direction, including tied outcomes;
this is consistency, not magnitude. Default order remains unchanged.

Browser verification compared the order of all 40 questions to an independent
Python calculation and checked range positions, native units, missing scores,
and phone-width layout. The update remains on the same review branch.

## All-group example follow-up

Benson requested all seven groups in each featured chart and selectable groups
for the saved-answer pairs. Each card now shows its full group chart, retaining
the same matched-model averages, original bounds, and native currency units.
Each answer column has an independent group selector; the model and saved
sample remain unchanged. The disclosure retains exact scores and answer counts
without repeating the chart already visible above it.

Browser verification checked all seven groups on all six charts and all 84
group/answer-column selections against the saved responses. Desktop and
390-pixel phone layouts passed visual review with no horizontal overflow or
JavaScript errors. Embedded study data is unchanged. Saved for local review;
not deployed.

## Evidence checks follow-up

Benson requested the same statistical scrutiny for the other five examples and
clear page labels, then asked whether significance alone was enough for this
benchmark. The response-level analysis and review are recorded in
`docs/example-analysis.md`. Four examples show group differences after an
adjustment for all 40 inspected prompts; salary is inconclusive, and the
daughter example has identical observed scores. The page labels these checks
exploratory and keeps size, per-model consistency, assumptions, and limitations
available alongside the statistical result. No claim of general benchmark
validation or general bias is implied by the test.

## P-value explanation follow-up

Benson requested removal of the repeated exploratory labels and a short,
plain-language hover explanation for p-values. Each example now has an
underlined p-value with contextual help explaining the null assumption,
smaller values, the 40-question adjustment, and the result's interpretation.
The exploratory-study description remains once in the methodology.

Verified all six hovers, keyboard focus, hoverable tooltip content, Escape,
outside dismissal, touch open/toggle/dismissal, and phone viewport bounds.
Desktop and phone screenshots were reviewed; embedded study data and
statistical results are unchanged.

## Example model selectors

Benson requested a model selector in each featured example. Each card now
switches its two first-saved-answer panels independently, retaining the chosen
groups and updating their accessible labels. Charts and statistical checks
continue to summarize the matched models. Browser checks verified 72 answer
combinations across all six cards/models, group changes after model changes,
independent card state, unchanged aggregates, and desktop/phone layouts.

Benson also asked why the 30-prompt subset toggle exists. It excludes the ten
prompts originally tagged more context-dependent. Checking both views confirmed
White remains lowest overall in all six models. The proposed simplification is
to put the robustness check in methodological details; the toggle has not been
changed without a request to do so.

## Prompt previews and subset placement

Benson approved moving the subset toggle into methodology details and requested
that hovering a group row substitute that group's wording into its example's
prompt. The toggle now sits inside the overall-score explanation alongside a
sentence stating that the main pattern survives the ten exclusions.

Each featured chart row previews the exact adjective/people wording from the
group definition in its own card. Repeated placeholders update together.
Idle placeholders use a full dashed outline and neutral fill; active wording
uses whole-surface contrast. Invisible sizing reserves each slot's largest
wording so hovering does not move the target row. Keyboard focus and touch
also preview a group, with reset on leaving or interacting elsewhere.

All 42 example/group previews were checked against the group definitions,
including both placeholder types, isolated card state, reset, and stable row
positions. Touch and keyboard checks passed; desktop/phone layouts and the
moved toggle were verified. The page export now includes the original people
wording as display metadata. All 56 tests pass; source scores are unchanged.

## Prompt preview refinement

Benson rejected the block treatment and requested text-only placeholders,
continuous hover areas, equal-height rows, and single-line group labels.
Placeholders now use muted monospace text; active wording uses a stronger
color and bold weight. Full-prompt invisible measurement copies reserve the
maximum paragraph height while allowing the visible words to flow naturally,
without fixed-width blank spaces around individual substitutions.

All chart rows are 34px tall with zero vertical gap and a 128px name column.
Moving directly between rows never resets the prompt to its placeholder state.
Pointer-path checks across all six cards at desktop and phone widths found
zero resets, gaps, wrapped labels, or layout shifts. Both layouts were visually
reviewed. Study data and statistical results remain unchanged.
