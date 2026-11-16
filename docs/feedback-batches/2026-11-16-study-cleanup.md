# 2026-11-16 reader-facing study cleanup

## Scope and decisions

Remove development history from the public study, then address Benson's wording,
chart-legibility, example-answer, accessibility, and sharing feedback. No new
study collection or changes to scoring/data. Preserve verbatim saved answers.
No new visible copy or features beyond the requested fixes.

## Work and acceptance

- About this test: retain scope, scoring, sample selection, and important limits;
  remove correction history, follow-up experiments, and internal configuration.
- Wording: Example answers; capitalize race category labels consistently; explain
  any omitted model in the relevant card; explain the 30-question subset and
  shuffled-label results in plain language.
- Statistics: independently verify the unique-bottom tally and standard-score
  bound before promoting or explaining them. Keep denominator/selection clear.
- Layout: pending Benson's reaction to full-width examples and shared model
  control versus retaining the two-column cards. Do not build the new layout
  until that response arrives.
- Salary: use the same dot language as other examples and a sensible labeled
  dollar scale; preserve the actual means and the inconclusive result.
- Accessibility: inspect rendered headings and table headers, fix real empty
  labels, and raise small chart labels without clipping at phone widths.
- Sharing: add a description and a preview image with deployment packaging.
- Verification: meaningful browser checks for controls/data, desktop/phone visual
  review, focused offline tests for affected computation, and one coherent
  publish only when authorized.

## Current progress

About copy cleaned locally. Independent read-only checks are examining the
statistical claims and the accessibility/metadata observations. Layout feedback
is pending. The earlier published study remains live.

## Verified findings and completed changes

- Unique-bottom counts: White 110, Asian 11, Indian 9, Native 5, Arab 4,
  Black 3, Hispanic 3. Denominator 192 complete nonconstant comparisons;
  37 all-race ties and 11 incomplete comparisons omitted. Of the 192, 47
  have a shared minimum, so the old generic “ties excluded” note was incorrect.
- Gemini 3.8 Flash gave explanations rather than a numeric firing rating in
  all 21 responses. The five-model card now names it and explains the omission.
- Population-standardized seven-category scores are bounded by ±sqrt(6),
  approximately ±2.45. Both overall charts now use that range and a visible unit;
  the details explain the example −1.1 anchor without claiming a harm scale.
- About text is study-only; category labels have consistent capitalization;
  answer labels say Example answers; the subset is described by its ten-question
  exclusion; the shuffle-test column has plain wording and a gloss.
- Salary's featured chart uses dots and a rounded $0–$150,000 scale.
- No empty live headings/table headers were reproducible (22 named headings,
  zero empty headings or table headers). Added a static title fallback. Chart
  labels are at least 12px; direction labels wrap safely on narrow phones.
- Description, Open Graph/Twitter metadata, and a 1200×630 PNG are included.
  The source preview is assets/share-card.html; deployment copies the PNG.

## Validation and pending work

All 56 offline tests passed. Browser checks confirmed the tally, exclusions,
headings, capitalization, salary dots, share-image response, and axis bounds at
1280px, 390px, and 320px. Desktop/phone screenshots and the PNG were reviewed.
The larger answer-card layout and control reduction still await Benson's reaction
to the proposed full-width/shared-selector versus two-column arrangement. These
changes are not deployed.
