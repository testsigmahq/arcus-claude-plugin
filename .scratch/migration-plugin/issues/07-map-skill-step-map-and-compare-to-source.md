# 07 — Map skill: the Step Map, compare-to-source, and Residue

**What to build:** The core of the whole plugin. Build the Step Map one distinct Source
Step at a time, and reuse each verdict everywhere that step occurs. A row carries the
source text, occurrence count, parameter shapes, the proposed expression, and a status, so
reviewing it does not mean going back to the source. One Source Step may map to several
Testsigma steps, because a source line that really does three things should not be forced
into one.

The part that earns this ticket its size is what makes a row finishable. The skill opens
the helper behind a source line and reads its sequence, and reports when that helper does
less than the line implies or more. It treats every wait, until, refresh and poll helper as
a loop until the source proves otherwise, because a helper that re-drives the interface
looks identical to a passive wait once flattened. It treats a wildcard or substring
comparison in the source as a question about what was being checked, not as licence to
write a weak comparison. A row cannot reach a finished state before that comparison has
happened.

Four of the six known faults were exactly this: a source line hiding a helper that did
something else. On the one occasion the comparison ran, it took about fifteen minutes and
found five of six. It is in this ticket rather than a later one because a check placed
after everything is a check that does not run.

Anything the format cannot express becomes Residue with a stated cause and the reasoning
that produced it, so a ruling can be overturned rather than hardening. One case already
believed unexpressible turned out to have a spelling nobody had found.

**Blocked by:** 03, 06

**Status:** ready-for-agent

- [x] Distinct Source Steps extracted with occurrence counts, mapped once, verdict reused at every occurrence
- [x] A row carries source text, occurrence count, parameter shapes, proposed expression and status
- [x] One Source Step may map to several Testsigma steps
- [x] The helper behind a source line is opened and its sequence reported, against the implementation rather than the surface syntax
- [x] A helper doing less than its line implies is reported as such, and so is one doing more
- [x] Every wait, until, refresh or poll helper is treated as a loop unless the source shows otherwise
- [x] A wildcard or substring comparison in the source raises a question rather than authorising a weak comparison
- [x] A row cannot be marked finished before the comparison has run
- [x] Residue entries carry a cause and the reasoning behind it, and can be reopened
- [x] Tests assert the skill's body requires opening the helper and requires the comparison before a row completes, and that no separate verification skill exists

**Done, 2026-09-04.** 254 tests pass. The mapping skill is 1,371 words, well inside
the progressive-disclosure budget, because the four Composite Step traps are stated
generically here and the format-specific detail stays in the adapter's Sequence
section. The Tosca adapter in ticket 11 will not need this skill rewritten.

The comparison is written as the exit condition of the stage rather than as a step
that follows it, which is ADR-0005's whole argument: a check placed after everything
is a check that does not run. A row that has not been compared stays `unreviewed`,
so the gate is the status rather than an instruction to remember.

Rows are ordered by occurrence count, highest first, because an early wrong verdict
on a frequent step is the most expensive mistake available.

Nine mutations verified, including two walk-backs of the class the last review
found, and all nine fail the suite.

**The residual gap is now demonstrated rather than predicted.** Review wrote a
walk-back in neutral procedural language — a row proceeding with its comparison
"noted as pending" instead of blocking — and the suite stayed green. It carries no
permissive vocabulary, so `hedges_in` cannot see it. I did not extend that list to
chase it: "does this document contradict itself" is not decidable by string
matching, and adding phrases would buy the appearance of coverage rather than
coverage. `hedges_in` now says so, and names the two controls that do cover it —
review, which found this one, and the behavioural evals of ticket 13, which test
what an agent does rather than what a document says.

**Two of my own absent guards rejected the honest document,** the fourth and fifth
instances this session. Good prose states a rule by contrast — "is a question, not a
licence", "No entry is final" — so a guard naming the inversion matches the rule
itself. Both replaced with positives an inversion must delete.

**The hedge check was polarity-blind too.** It flagged "they set the floor cost and
are not optional", which is the opposite of granting permission. Narrowed the entry
from `optional` to `is optional`.

**Ticket 8's boundary held.** The only element mention here is "an unresolved
element" as a Residue cause distinct from an unexpressible step. No locator work
leaked in, and nothing ticket 8 needs is missing.
