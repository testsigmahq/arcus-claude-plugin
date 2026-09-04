# 11 — Tosca adapter, and Element Resolution as its own Phase

**What to build:** The second Source Adapter, and the Phase that only a source like this
one needs.

A Tosca subset export is gzipped JSON: one flat list of entities, each with a class, a
unique surrogate, string attributes, and associations to other entities by surrogate. Two
properties of it drive the adapter. First, order exists nowhere as a value. No entity
carries an order, index or sequence attribute, and the only ordering signal is the position
of a surrogate inside an association list, so a reader that walks the entity list in file
order produces a scrambled sequence that looks complete. Second, the export is
transitively closed, so the reusable blocks a test references travel with it and true
sequence is recoverable from the file alone.

It carries no locators of any kind. Not one. That is what forces Element Resolution into a
separate Phase here, where for a page-object source it is part of mapping. This adapter is
therefore also the ticket that proves the Phase structure follows the source rather than
being fixed.

Values in this source carry their own small language, so a single value can encode a
sequence of several actions with no helper anywhere to open. That is the second shape of the
composite-step problem and the mapping skill has to read it as a sequence.

**Blocked by:** 02, 08

**Status:** ready-for-agent

- [x] The adapter declares all three properties: sequence not hidden behind a helper, no locators carried, values do carry their own language
- [x] The adapter states that order comes from association list position, and that walking the entity list instead is wrong
- [x] Reusable block references are resolved so true sequence is recovered from the export alone
- [x] A value written in the source's own language is read as a sequence of actions
- [x] A wildcard comparison in the source raises a question rather than becoming a weak comparison
- [x] Element Resolution runs as its own Phase for this source, and the element names the Step Map references are carried forward for it to satisfy
- [x] A data-driven test is recognised as a template plus instances, so the template is migrated rather than producing one duplicated test per instance
- [x] Demonstrated against a real export: correct step order recovered, and the absence of locators reported rather than silently producing none

**Done, 2026-09-04.** 462 tests pass, arcus untouched at 92. The two shipping adapters
now differ on all three declared properties, which a test asserts — so the pair covers
the property space and a third adapter is not needed for coverage.

**I could not reproduce the spec's own claim, and wrote the weaker true thing.** The
spec says walking the entity list "produces a scrambled sequence that looks complete".
For the one populated test case in the real export, file order agrees with recovered
order at every one of 53 adjacent pairs. Zero inversions. So the adapter says instead
that no entity carries an order attribute — there is nothing to sort by — and that 8
of the 48 steps are reachable from no test case, so a flat walk yields steps belonging
to no test. Then the hedge that matters: file order agreeing here is a coincidence of
this file, and the format offers no attribute that would let a reader check the
agreement. An adapter is read by a Migration that will trust it, so an overstated
claim there is worse than a missing one.

The synthetic fixture demonstrates what the real export happens not to: its recovered
order and its file order differ.

**Two findings came from the evidence rather than from reasoning.** The entity graph
cycles — found by `RecursionError`, so resolving reusable-block references needs a
visited set, and that is now a rule. And a real module is named `M&T Org Search |
CHIP`, whose pipe exposed a false claim in this suite's own helper: `parse_count_table`
documented that backticks protect a cell containing a pipe. They do not. The row
parsed as three cells and was dropped from the counts silently — a short table with
nothing said. Fixed to honour `\|`, docstring corrected, regression tests added.

Review re-derived all 25 numeric claims independently and found one wrong.

**The token counts required a normalisation the adapter never stated.** 13 distinct
tokens, `CLICK` at 47: true only under case-folding and argument-stripping. Literally
there are 17 spellings, and the export writes the same action `{Click}` 43 times and
`{CLICK}` 4 times — so `{CLICK}` at 47 was presented as a literal count and was not
one. This is precisely the class I had called worse than a missing claim, in my own
document. The rule is now stated, with both figures given and the reason the rule is
needed rather than tidy.

**A cross-document contract was broken.** `migration-directory.md` and `resume.md` both
depend on `migration.md` gaining an Element Resolution section, whose absence is how a
later session knows the Phase is open. Nothing wrote it. An agent following
resolve-elements to completion would resolve everything, commit, and `resume` would
name element resolution as the active Phase forever. Now written, and tested.

**Criterion 8 rested on arithmetic done once by hand.** Added `tests/tosca.py` — test
tooling only, mirroring `gherkin.py`, since ADR-0004 forbids shipping a parser — plus
a synthetic fixture carrying every trap, and checks of every stated number against the
real export, skipped when that file is absent. Changing one table cell now fails the
suite. The fixture always runs and needs no customer data.

Fourteen mutations verified, all caught. Two survived first: both intra-paragraph
coincidence, where the paragraph explaining why a rule matters reuses the rule's own
vocabulary.
