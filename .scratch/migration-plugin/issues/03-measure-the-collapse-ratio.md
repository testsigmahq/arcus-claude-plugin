# 03 — Measure the Collapse Ratio of the evidence suite

**What to build:** The one number the whole mapping approach rests on and nobody has
measured. Mapping each distinct Source Step once and reusing the verdict is only
affordable if source steps repeat. Apply the Cucumber adapter's normalisation rule to the
suite that produced the six faults, and report the total step count, the distinct count,
their ratio, and the size of the long tail that occurs exactly once.

The long tail matters as much as the ratio. Steps appearing once cannot amortise anything,
so they set the floor cost of a Migration.

**Blocked by:** 02

**Status:** ready-for-agent

- [x] Total source step occurrences and distinct Source Step count both reported, with the normalisation rule stated so the number is reproducible
- [x] The ratio reported, along with the count of Source Steps occurring exactly once
- [x] The most frequent Source Steps listed with their counts, so the shape of the vocabulary is visible and not just its size
- [x] A stated conclusion on whether per-distinct-step comparison is affordable for a suite of this shape
- [x] If the ratio is near 1.0, say so plainly, because that is a reason to reconsider the mapping design rather than a number to file

**Done, 2026-09-03.** Full report in `../collapse-ratio.md`.

2,759 step lines, 351 distinct Source Steps, a Collapse Ratio of **7.86**, 138 Source
Steps occurring exactly once. Not near 1.0 and not marginal, so the mapping Phase's
central assumption holds for a suite of this shape.

The handoff's structural claims were re-derived rather than trusted and all hold: 35
scenarios, no `Scenario Outline`, no `Examples`. Also no `Background` blocks and no
`Rule:` blocks, which nobody had recorded.

Two numbers matter more than the ratio. Eighty Source Steps, 23% of the vocabulary,
cover 80% of occurrences. And the 138 singletons are 39% of the vocabulary for 5% of
the step lines, which argues for mapping the tail lazily rather than completing the
Step Map before assembly starts.

The most useful number was not asked for: **only 65 of 351 Source Steps genuinely
vary.** 219 carry no parameter at all and 67 carry one the suite only ever fills a
single way. Rows are not equal, so a plan built on an average row will mis-order the
work.

**Four findings that change other tickets.** Almost a fifth of the suite is API rather
than UI, 29 distinct steps carrying 511 occurrences, which have no page object and no
locators. The probable-loop population is five times larger than the handoff
suggested. Element Resolution has a size for the first time: one step's three variants
name 108 controls across 38 screens, so element work is not proportional to Source
Steps. And eight steps carrying 72 occurrences form one `Validate <entity> status`
family that is one design decision repeated eight times.

**Audited independently, and the audit found three real errors.** The API classifier
missed four steps carrying 40 occurrences that say "Json" rather than "response", and
wrongly counted a UI filter that mentioned a payload; corrected from 26/472 to 29/511.
The report highlighted 50 occurrences of a probable loop while silently excluding
`Wait for page loading` at 133, which is the largest wait-shaped step in the suite and
exactly what the adapter's own rule says not to exclude by intuition. And the
affordability section presented the eight-times comparison as a second argument when
holding minutes-per-unit constant makes it a restatement of the ratio. All three
corrected, and the sixty-hour figure is now stated as a floor on reading rather than
an estimate of the job.

The audit also disputed the element figures, giving 516 occurrences and 105 pairs
against my 521 and 108. It was measuring two variants; a third exists, `in mobile
apk`, occurring five times. Verified against raw lines and 521 stands. The audit did
find that two of the 38 screen names differ only in case, so the real screen count is
37 and one is a typo the Migration must resolve.

Two generalisable lessons went back into the Cucumber adapter: classify a step as API
or UI by reading it rather than by keyword, and report the parameterisation profile
alongside the ratio.
