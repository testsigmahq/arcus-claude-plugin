# Spec — deliver a Migration one Conversion at a time

Status: ready-for-agent. Not published to a tracker; local, alongside `spec.md`.
Derived from the `/grill-with-docs` session of 2026-09-14. Vocabulary is from
`plugins/testsigma/CONTEXT.md`; decisions are constrained by ADR-0012, which
this spec implements, and by ADR-0001, ADR-0002, ADR-0004, ADR-0005 and
ADR-0011, which it leaves intact.

This spec amends the plugin built by `spec.md`. It changes the order in which a
Migration does its work. It changes nothing about what a converted test must be,
and it weakens no check.

## Problem Statement

An Operator is onboarding a customer onto Testsigma. The customer's suite holds
up to 1,000 test cases of 30 to 60 steps each — 30,000 to 60,000 source step
lines.

The plugin as built maps the whole suite before it assembles anything. Mapping
is gated on a human-grade reading of the helper behind every distinct Source
Step, and at this size the distinct set is 1,000 to 3,000 rows even after
collapse. At any honest rate per row, that is weeks of work before a single
`.sigma` test exists.

For the Operator the consequence is not that the Migration is slow. It is that
there is nothing to show. A customer who has just committed to Testsigma gets
weeks of silence, no working test, and no evidence the work is going anywhere.
The plugin's own progress number — rows reviewed of total distinct — is
meaningful to the Migration and means nothing to the customer, who counts tests.

A second consequence compounds it. Under the current order, one question the
Operator has not answered can hold up everything, because a Phase blocks the
next and nothing downstream may start.

## Solution

A Migration delivers in **Conversions**. A Conversion is the end-to-end work on
one source scenario: map the Source Steps it reaches, resolve the elements those
steps name, assemble the test, check it, commit it. Then stop.

Survey is unchanged and still blocks everything — the adapter must be chosen,
the snapshot pinned and the vocabulary enumerated before anything can be
converted. Mapping and assembly stop being Phases of the Migration and become
the steps inside a Conversion.

The Step Map stays one shared table and fills progressively, so a Source Step
decided in one Conversion is free in every Conversion after it. The economics
that made mapping worth doing are untouched; only the order changes. The
Operator sees a working test on the first day, and a delivered count that rises
from then on.

Because judgement is cheapest to correct early, the first Conversions are chosen
by greedy set cover — the scenario introducing the most unseen Source Steps —
until the next one would introduce fewer than about three. After that the order
is whatever the Operator's priority is.

A Conversion that needs something only the Operator can give is **parked**, and
the loop takes the next one. No single unanswered question stalls a Migration
again.

## User Stories

1. As an Operator, I want a working Testsigma test on the first day of a
   Migration, so that the customer sees evidence the work has started.
2. As an Operator, I want to be told how many tests have been delivered out of
   how many scenarios, so that I can report progress in the customer's terms.
3. As an Operator, I want to keep seeing rows reviewed of total distinct, so
   that I can tell a Migration that is working from one that is reading source
   and writing nothing.
4. As an Operator, I want to be told why the third Conversion took an hour and
   the three-hundredth took four minutes, so that I can forecast the rest.
5. As an Operator, I want a Conversion that needs an answer from me to be parked
   rather than to stop the Migration, so that one open question does not cost
   the customer a week.
6. As an Operator, I want to see which Conversions are parked and what each is
   waiting on, so that I know what only I can unblock.
7. As an Operator, I want a parked Conversion to be taken up again once I have
   answered, so that nothing I unblock is forgotten.
8. As an Operator, I want the scenarios survey ruled unconvertible to be visibly
   out of scope rather than absent, so that I can tell "somebody looked and
   ruled it out" from "nobody looked".
9. As an Operator, I want the earliest Conversions to be the ones that teach the
   Migration the most vocabulary, so that later ones get cheaper fastest.
10. As an Operator, I want to be told when the Migration switches from
    vocabulary-first ordering to my own priority, so that I know I can start
    naming what I want next.
11. As an Operator, I want to name which scenarios matter most once vocabulary
    has settled, so that the customer gets the tests they actually care about
    first.
12. As an Operator, I want one command to tell me which Conversion is next and
    whether anything is waiting on me, so that picking the work up is not
    archaeology.
13. As an Operator, I want a Migration resumed weeks later to know exactly what
    is done, pending and parked, so that no session re-derives it.
14. As an Operator, I want a Source Step decided once to be reused by every
    scenario after it, so that the Migration gets cheaper as it goes.
15. As an Operator, I want a Source Step whose decision is later found wrong to
    be corrected everywhere it was used, so that the suite never keeps tests
    built on a ruling I have since overturned.
16. As an Operator, I want a corrected Source Step to return the affected
    scenarios to pending, so that the delivered count never counts a test built
    on a superseded decision.
17. As an Operator, I want a re-opened scenario to go back through the same
    loop, so that there is one path to a delivered test and not two.
18. As an Operator, I want each Conversion committed as it finishes, so that a
    session that ends early loses nothing.
19. As an Operator, I want the helper behind every source line opened and
    compared before a row is called reviewed, exactly as before, so that
    delivering sooner does not mean checking less.
20. As an Operator, I want elements resolved while the source is already open,
    so that finding controls costs one reading and not two.
21. As an Operator, I want the Migration to look in the target project before it
    asks me to capture anything, so that my attention is spent only where
    nothing else can answer.
22. As an Operator, I want to be asked for a whole screen's elements at once
    rather than one at a time, so that capture costs me one visit per screen.
23. As an Operator, I want a Conversion to perform exactly one scenario and
    stop, so that each session's reasoning stays sharp on the judgement calls
    that matter.
24. As an Operator, I want everything a fresh session needs to be in the
    Migration Directory, so that the previous session's context is never
    required.
25. As an Operator, I want the ordering of Conversions computed rather than
    guessed, so that two sessions do not choose differently from the same state.
26. As an Operator, I want to know which scenarios a corrected row affects
    without anyone reading the whole working copy, so that correction is cheap
    enough to actually happen.
27. As an Operator, I want Residue to assemble as a marker and not park a
    Conversion, so that a step the format cannot express does not cost me a
    whole test.
28. As an Operator, I want a Concession recorded on the row as before, so that a
    known difference is never mistaken for an unnoticed one.
29. As a maintainer, I want the mechanical parts of the loop to be scripts, so
    that they are unit-tested rather than asserted as prose an agent may skip.
30. As a maintainer, I want the document contract tests to cover the new skill
    and the changed ones, so that a later edit cannot quietly remove a rule.
31. As a maintainer, I want eval cases for the behaviours that only an agent can
    get wrong, so that "performs one Conversion and stops" is measured, not
    hoped for.
32. As a maintainer, I want `resolve-elements` to stop advertising itself as the
    way into a Phase, so that nothing invokes it as a bulk stage.
33. As a maintainer, I want the two new Migration Directory files declared in
    one place, so that every test and skill reads the same file set.

## Implementation Decisions

**The glossary and the ADR are already written.** `CONTEXT.md` defines
`Conversion` and `Parked`, redefines `Phase` so survey is the only one, corrects
`Step Map` (it no longer claims to be built once per Migration), and redefines
`Element Resolution` as something that happens inside a Conversion rather than
as a stage. ADR-0012 records the decision, the rejected alternatives and the
consequences. Implementation must not contradict either.

**Two new Migration Directory files**, both declared in the reference that fixes
the file set, and both added to the single constant the tests read:

- **`scenarios.md`** — written by survey, mechanically. One row per source
  scenario: the scenario, the Source Steps it reaches (the incidence), a status
  of `pending`, `done`, `parked` or `out-of-scope`, and a `Reason` used by
  `parked` and `out-of-scope` alike. It is both the incidence and the Conversion
  queue, so one read answers "what is left" and "what would it cost".
- **`assembled.md`** — written by assembly. One row per assembled test: the
  scenario, the test, the row versions it consumed, and when. This is what makes
  a corrected row's dependents findable without re-reading the working copy.

The **unseen count is never stored**. It is computed on demand from
`scenarios.md` and `step-map.md`, because a stored count is stale the moment any
Conversion finishes, and a stale count silently mis-orders the queue.

**`step-map.md` gains a `Version` column**, placed beside `Status`. It is bumped
only when the row's Expression or Status changes. Occurrence counts and
provenance change constantly as new scenarios are met, and a version churning on
those would re-assemble the suite for nothing.

**A new `convert` skill** performs exactly one Conversion and stops. It reads the
Migration Directory, picks the next scenario, runs mapping for the Source Steps
that scenario reaches, resolves their elements, assembles the test, runs the
stage's checks, records and commits, then reports. It owns the queue, the
ordering and the re-queue trigger — none of which belong to `map` or `assemble`.

**`map` and `assemble` survive as skills and are called by `convert`.** Both
carry measured rules that merging would risk losing. `map`'s Step 0 already
scopes its call-chain expansion to a scenario, which is exactly a Conversion, so
that rule is unchanged. `assemble` is already scenario-at-a-time.

**Three mechanical pieces become scripts**, joining the existing `check_*`
family, because each is exact by construction in the same sense survey's
enumeration is:

- computing the unseen count per scenario and selecting the next Conversion by
  greedy set cover
- deciding which scenarios a version bump invalidates, by reading `assembled.md`
- checking `scenarios.md` status consistency — that no scenario is `done`
  without an `assembled.md` row, none is `parked` without a `Reason`, and none
  is both

**Ordering has two stages with a measured switch.** Greedy set cover until the
next scenario would introduce fewer than about three unseen Source Steps, then
Operator priority. The threshold is measured rather than a fixed count, because
a fixed count guesses at a suite's shape. The switch is reported when it happens.

**Survey changes in two ways.** It emits the scenario-to-Source-Step incidence
it currently computes and discards, and it seeds `scenarios.md` alongside
`step-map.md`. It continues to seed every distinct Source Step as `unreviewed` —
the denominator and the anti-stall signal both depend on the empty rows existing
to be visibly unfilled. Scenarios it screens as unconvertible are seeded
`out-of-scope` with the reason, never omitted.

**Element resolution happens inside a Conversion, in three places in order:**
the source, then the target project, then the Operator. Where the adapter
declares `carries-locators: yes` the first place answers, in the same reading
that recovers sequence — unchanged from today. A Conversion parks only when all
three are exhausted, which for a page-object source should essentially never
happen. When it does park, the whole screen is put to the Operator, not the one
element that blocked it.

**`resolve-elements` keeps its procedure and loses its framing.** Its
description currently declares it the way into a Migration Phase; it becomes
something `convert` calls, scoped to one screen.

**`resume` replaces its Phase line with the Conversion queue** — done, pending,
parked with reasons, and which Conversion it would take next. A Phase line
reading "converting" for three weeks is noise in front of the question a fresh
session actually asks. It stays read-only.

**A finished Conversion reports**, in this order: the test delivered; tests
delivered of total scenarios; rows reviewed of total distinct; rows new versus
reused this Conversion; any Concession or Residue recorded; whether anything
parked. The first is the onboarding number; the second explains the cost curve.

**Everything shown to the Operator still obeys `references/asking.md`** — no
code, no file path, no stack trace, no diagnostic code. The new reporting and
the new queue are not exempt.

## Testing Decisions

A good test here asserts what a document *requires* or what a script *decides* —
never how either is worded or structured internally. The plugin is made of
markdown, so the document tests check that a rule is present and binding, not
that a particular sentence exists. Prior art is throughout `tests/`, which
already does exactly this for every existing skill.

**Document contract tests, through the existing `support.py` seam.** Prior art:
`test_map_skill.py`, `test_assemble_skill.py`, `test_documents.py`,
`test_skills.py`. Covers: the `convert` skill's required sections and its
one-Conversion-and-stop rule; survey emitting incidence and seeding
`scenarios.md` including `out-of-scope` rows; `resolve-elements`' changed
description; `resume` reporting the queue; the two new files present in
`MIGRATION_DIRECTORY_FILES` and in `migration-directory.md`; the `Version`
column; the `Conversion` and `Parked` terms in `CONTEXT.md`; ADR-0012 present
and tracked. The existing hedge check (`PERMISSIVE_HEDGES`) applies to `convert`
as to every other skill.

**Script unit tests.** Prior art: `test_call_chain_check.py`,
`test_coverage_check.py`, `test_step_order.py`, `test_committed_check.py`.
Covers: set-cover selection picks the scenario with the most unseen Source Steps
and reports the switch at the threshold; invalidation from `assembled.md`
returns exactly the scenarios that consumed a bumped version and no others;
status consistency rejects `done` with no assembled row, `parked` with no
reason, and contradictory states. Ordering must be deterministic — two runs over
the same state select the same scenario, including at a tie.

**Eval cases.** Prior art: the existing `evals/` cases and their
`migration-part-done` fixtures. Covers only what an agent can get wrong and a
document test cannot see: that `convert` performs one Conversion and stops
rather than looping; that a Conversion needing an Operator answer parks and the
next one is taken rather than the run stalling; that changing a row's Expression
bumps its version and returns dependent scenarios to `pending`; that Residue
assembles as a marker without parking. Fixtures extend the existing
`migration-part-done` shape with `scenarios.md` and `assembled.md` rather than
introducing a new fixture family.

**Every eval case must discriminate.** Recent commits on this branch fixed three
cases that scored identically across arms; a new case that cannot distinguish
the behaviour it names is not a test.

## Out of Scope

- **Weakening any check.** Tiering compare-to-source by occurrence was
  considered and rejected in ADR-0012. Every row that is reached gets the same
  reading it gets today.
- **Parallelising Conversions across agents.** Rejected on the measured evidence
  in `fault-classes.md`. One Conversion per invocation, sequential.
- **Changing what a converted test must be.** Document order, block nesting,
  element resolution rules, Residue causes, Concession recording and the check
  order are all unchanged.
- **Changing survey's refusals or its platform gate.** Untouched.
- **New Source Adapters.** The change is format-independent.
- **A tracker migration.** This spec stays local beside `spec.md`, as that one
  did.
- **Automating the Operator's priority order.** After the set-cover stage the
  order comes from the Operator; the plugin does not infer it.
- **Retrofitting Migrations already in progress.** No migration path for a
  Migration Directory written before this change.

## Further Notes

The rework obligation is not new. `migration-directory.md` already says a row
that fails re-check "stops being `reviewed` and is worked again, along with
every test already assembled from it." Under whole-suite Phases no test existed
yet when a row was revised, so the rule was unreachable. Conversions make it
reachable, and `assembled.md` is what makes it actionable. This spec adds the
machinery for a policy the plugin already held.

Ordering by scenario preserves most of what ordering by occurrence bought.
A Source Step occurring 2,000 times appears in nearly every scenario, so any
scenario order front-loads the frequent rows. Set cover is an improvement on
that, not a replacement for something lost.

The cost curve is itself the thing to show the customer. The first Conversion
may take most of a day; by the fiftieth most rows are reuse; by the
three-hundredth a Conversion is minutes. Reporting both progress numbers is what
makes that curve visible rather than surprising.
