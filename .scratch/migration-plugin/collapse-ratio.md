# Collapse Ratio of the evidence suite

Measured 2026-09-03 against the Cucumber suite that produced the six faults, using
the normalisation rule in `plugins/testsigma/adapters/cucumber-java.md` as
implemented in `plugins/testsigma/tests/gherkin.py`. Ticket 3.

Source: the 16 feature files of the MAWM Selenium suite, now under version control.
Reproduce with the gherkin module against that suite's `FeatureFiles` directory; the
rule is stated in the adapter so the number does not depend on this run.

## The headline

| | |
|---|---|
| Total step lines | 2,759 |
| Distinct Source Steps | 351 |
| **Collapse Ratio** | **7.86** |
| Source Steps occurring exactly once | 138 |

**The ratio is not near 1.0, and it is not marginal.** Every distinct Source Step is
written on average nearly eight times, so mapping once and reusing the verdict does
roughly an eighth of the work that mapping each occurrence would. This is the
assumption the whole mapping Phase rests on, and for a suite of this shape it holds
comfortably.

## Structural cross-checks

The handoff's claims about this suite were re-derived rather than trusted, and all
hold: 35 scenarios, zero `Scenario Outline` and zero `Examples` blocks. Also zero
`Background` blocks, which the handoff did not mention and which removes a
counting question entirely.

## Where the work actually is

| Occurs | Distinct Source Steps |
|---|---|
| once | 138 |
| 2 to 5 times | 127 |
| 6 to 20 times | 60 |
| 21 or more times | 26 |

Two numbers matter more than the ratio.

**Eighty distinct Source Steps, 23% of the vocabulary, cover 80% of all
occurrences.** So most of the suite becomes mappable early, and progress will look
fast before it looks slow.

**The 138 singletons are 39% of the vocabulary and 5% of the step lines.** Each costs
a full Step Map row and a full comparison against source, and buys one step line.
That is where the economics invert, and it argues for mapping the tail lazily, when a
scenario actually needs a row, rather than completing the Step Map before assembly
starts.

The ten most frequent, which are what a migration will meet first:

| Occurrences | Source Step |
|---|---|
| 459 | `Click "<param>" on "<param>" WaitForPageLoading` |
| 133 | `Wait for page loading` |
| 96 | `Click on Row At First Index` |
| 89 | `Verify text "<param>" from "<param>" on "<param>"` |
| 80 | `API send "<param>" request` |
| 80 | `Verify the response code is "<param>"` |
| 57 | `Click "<param>" on "<param>"` |
| 56 | `Set Request specification and Request Body for POST request for endpoint "<param>" and file "<param>"` |
| 56 | `Verify the expected value "<param>" equals in response using the jsonpath "<param>"` |
| 44 | `Store generated TestData value "<param>" into global get variable "<param>"` |

## Is the ratio an artefact of the rule?

A ratio can be inflated by a rule that splits steps it should merge, so both
directions were checked against this suite.

**Under-collapse: none found.** No pair of distinct Source Steps differs only by a
trailing plural, and no pair differs only by letter case. Comparing
case-insensitively gives 351 distinct steps, the same number, so the ratio of 7.86
holds either way. The singular/plural limitation the adapter documents is real in
principle and has zero instances here.

**Over-collapse: one real instance, and it matters.** `API send "<param>" request`
occurs 80 times and its parameter is the HTTP method: 56 POST and 24 GET. That is
one Source Step covering two genuinely different actions, so a single Step Map row
has to express both. The rule is not wrong to collapse it, since the source really
did write one phrasing, but the row is two rows of work wearing one row's clothes.
Expect a handful more of this shape.

## How much of the vocabulary is actually parameterised

| | Distinct Source Steps |
|---|---|
| No quoted parameter at all | 219 |
| Parameterised, but only ever one value used | 67 |
| Parameterised with several values | 65 |

This is the most useful number in the whole measurement and it was not asked for.
**Only 65 of 351 Source Steps genuinely vary.** 219 are fixed phrasings, and another
67 take a parameter the suite only ever fills one way, such as
`Verify the response code is "<param>"`, which occurs 80 times and is always 200.

A fixed phrasing is a much cheaper Step Map row than a parameterised one: there is
one expression to write and no parameter shape to reason about. So the cost of the
Step Map is not 351 equal rows. It is roughly 65 hard rows, 67 easy ones that should
be confirmed rather than designed, and 219 straightforward ones.

## Affordability: yes, decisively

Per-distinct-Source-Step comparison is affordable for a suite of this shape. At 351
rows rather than 2,759 occurrences, even a generous ten minutes per row of reading the
helper and comparing against it is on the order of sixty hours. Per occurrence it
would be roughly eight times that, which is not a job anyone would finish.

Two qualifications on that conclusion.

It is affordable **relative to the alternative**, not cheap. 351 reviewed rows is
still weeks of work, and it is the floor: the ratio bounds the reading, not the
judgement.

The ten-minutes-a-row figure is also the wrong shape, now that the parameterisation
profile is known. Rows are not equal. 65 genuinely parameterised rows carry most of
the design effort, and the 219 fixed phrasings are closer to confirmation than to
design. A schedule built on an average will mis-order the work; the parameterised
rows are where the Composite Steps and the judgement calls concentrate.

**And the eight-times comparison is not a second argument.** Holding minutes-per-unit
constant across both denominators makes "per occurrence costs eight times per row" a
restatement of the ratio, not independent support for it. The ratio is the finding.
The hours are an illustration of it, and reading them as corroboration would be
double-counting one measurement.

**Sixty hours is a floor on reading, not on effort.** It prices the Step Map rows and
nothing else. It does not price Element Resolution, which this report has just shown
is uncorrelated with row count: one row alone names 108 controls across 38 screens.
It does not price the assembly of 35 scenarios, the Operator questions, or the
comparison of each assembled test's document order. Anyone planning from this number
should read it as the smallest part of the job that can be estimated yet, rather than
as an estimate of the job.

The tail should be **deferred, not skipped**. Completing all 351 rows before assembly
begins spends 39% of the effort on 5% of the suite before a single test is assembled.

## Four things this measurement found that nobody had recorded

**Almost a fifth of the suite is API, not UI.** 29 distinct Source Steps, 8.3% of
the vocabulary, account for 511 occurrences, 18.5% of all step lines: sending
requests, asserting response codes, reading values by JSON path, minting access
tokens. These have no page object and no locators, so the Cucumber adapter's
`carries-locators: "yes"` is a statement about its UI steps and says nothing about
these. An API step is a different mapping target with a different shape. Worth
deciding before ticket 7 rather than during it.

Those figures are the corrected ones, and how they were wrong is the more useful
finding. A first pass classified API steps by keyword and reported 26 steps and 472
occurrences. It missed four steps carrying 40 occurrences that say "Json" rather than
"response" or "jsonpath", among them
`Verify the attribute "<param>" with value "<param>" is present in Json Object
"<param>"`, which is the very step whose weakening to a substring match was one of the
six original faults. It also wrongly counted `Filter by Payload "<param>"`, a UI
filter field that matched on the word payload.

**So classifying a Source Step is judgement, not a pattern.** A keyword rule over step
text will always miss the synonym and catch the homonym, and it did both here. This
belongs in the mapping stage where a person or an agent reads the step, not in a
classifier that runs before anyone looks.

**The probable-loop population is five times bigger than thought.** The handoff named
refresh-until as the only genuine loop. The wait-shaped vocabulary is broader: `Wait
and Validate Order status is "<param>"` occurs 42 times, with ASN and Labor Message
variants adding 8 more, and the explicit `Click refresh until …` shapes add 8. A step
named "Wait and Validate" that polls a status is exactly the shape that flattens into
a passive wait and still passes. That is 50 occurrences of a probable loop that the
handoff's account would not have flagged.

Two much larger wait-shaped steps sit outside that count and need a decision rather
than silence, because the adapter's own rule says treat anything named wait, until,
refresh or poll as a loop until the source proves otherwise:

| Occurrences | Source Step | Likely nature |
|---|---|---|
| 133 | `Wait for page loading` | Synchronisation, not business logic |
| 10 | `Wait for <number> seconds` | A fixed sleep |
| 2 | `Click on Refresh and Row at First Index` | Names refresh, is not a poll |

`Wait for page loading` is the single largest wait-shaped step in the suite, larger
than the 50 highlighted above, and excluding it by intuition is exactly the move the
rule exists to prevent. It almost certainly maps to nothing at all, because the target
platform waits for page load itself, but that has to be established by reading the
helper once and then applied 133 times, not assumed.

**Element Resolution has a size for the first time.** The generic click step has
three variants, plain, `WaitForPageLoading`, and `in mobile apk`, occurring 57, 459
and 5 times, 521 together. Between them they carry 108 distinct
control-and-screen pairs across 38 named screens.

Two cautions on those figures. Measuring only the two frequent variants gives 516
occurrences, 105 pairs and 36 screens, and the third variant is easy to miss because
it occurs five times; an independent audit of this report did miss it. And two of the
38 screen names differ only in case, `OrdersPage` and `Orderspage`, so the real screen
count is 37 and one of them is a typo the Migration will have to resolve as either one
screen or two. Source data defects of that kind become Application Facts. The converted
scenario used 8 screens and 46 elements, so it exercised roughly a fifth of the
screens. The element vocabulary is separate from the step vocabulary and does not
collapse with it: one Source Step occurring 459 times still names 108 different
things to find. Any estimate that treats element work as proportional to Source Steps
will be badly wrong.

**One family should be mapped as a pattern, not as rows.** Eight distinct Source
Steps carrying 72 occurrences match `Validate <entity> status "<param>"`, over OLPN,
ASN, Task, Orders, ILPN, Allocation and LPNs, and seven of the eight share one shape.
They are legitimately distinct steps, since each checks a different business object,
so this is not a normalisation failure. But they are one design decision repeated
eight times, and mapping them independently would be eight separate judgements about
what is really one pattern. Expect the Step Map to want a notion of a family.

## Note on where this belongs

In a real Migration these numbers are a Platform-independent fact about the source and
belong in the Migration Directory inside the source suite, per ADR-0002. They are here
instead because they are input to the plugin's design rather than the output of a
Migration, and because another session owns that path.
