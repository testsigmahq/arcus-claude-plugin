# Convert one scenario at a time, not one Phase at a time

A Migration delivers in **Conversions**: one source scenario taken end to end —
mapped, its elements resolved, assembled, checked, committed — before the next
one starts. Survey remains a Phase and still blocks everything. Mapping and
assembly stop being Phases of the Migration and become the steps inside a
Conversion.

The Step Map stays one shared table and fills progressively, so a Source Step
decided in one Conversion is reused free by every Conversion after it. The
economics that made mapping worth doing are unchanged; only the order is.

## Considered Options

The plugin's original order was map the whole suite, then assemble it. That was
designed against a suite of tens of scenarios, and it holds there.

It does not hold at the size this was measured against: up to 1,000 test cases
of 30 to 60 steps, or 30,000 to 60,000 source step lines. Vocabulary saturates
as a suite grows, so the Collapse Ratio rises with size — but even at a ratio of
20 to 40 that is 1,000 to 3,000 distinct Source Steps, each gated on a
human-grade reading of the helper behind it. Nothing would be delivered for
weeks. For a customer onboarding onto Testsigma, that is not a slow start; it is
an unbroken silence with no evidence that the work is going anywhere.

A second alternative was to keep the Phase order and weaken the check that gates
each row — tier the compare-to-source comparison by occurrence, giving the
singleton tail something less than a full reading. It was rejected because
Conversions achieve the same saving honestly: a row is only ever met when a
scenario needs it, so the tail costs nothing until it is reached, and no row
that is reached gets a weaker check than before. Four of the six measured faults
in the conversion that produced this plugin were found by that comparison and by
nothing else.

A third was to keep Phases and parallelise mapping across agents. Rejected on
the evidence in `fault-classes.md`: four subagents sent to read step definitions
returned summaries, and a summary of a helper is the surface again.

## Consequences

**Rework becomes possible, and must be mechanical.** A row decided in one
Conversion can be revised by a later one, and every test already assembled from
it is then built on a decision since ruled wrong. This is not a new rule —
`migration-directory.md` already says such a row "stops being `reviewed` and is
worked again, along with every test already assembled from it" — but nothing
could find those tests. So:

- `step-map.md` gains a `Version` column, bumped only when a row's Expression or
  Status changes. Occurrence counts and provenance change constantly as new
  scenarios are met, and a version that churned on those would re-assemble the
  suite for nothing.
- `assembled.md` records, per assembled test, the row versions it consumed.
- A bump returns the affected scenarios to `pending`, and they are re-taken as
  Conversions through the same loop. A re-opened scenario visibly goes back to
  pending, so the delivered count stays honest.

**Order of Conversions matters.** Taking scenarios in an arbitrary order still
front-loads the most frequent Source Steps, because a step occurring 2,000 times
appears in nearly every scenario. But the first Conversions are where judgement
is cheapest to correct, so they are chosen by greedy set cover — the scenario
introducing the most unseen Source Steps — until the next one would introduce
fewer than about three, at which point the ordering hands over to whatever the
Operator's priority is. Survey therefore records the scenario-to-Source-Step
incidence it currently computes and throws away, in `scenarios.md`.

**An outstanding question no longer stalls the Migration.** A Conversion that
needs something only the Operator can give is *parked*, and the loop takes the
next one. Under Phases a single unanswered question could hold up everything,
which is the failure this ADR exists to prevent.

**One Conversion per invocation.** `convert` performs exactly one and stops, so
each session starts from the Migration Directory and nothing else. A loop would
accumulate every scenario's source reading in one window, and by the tenth the
judgement calls this plugin exists to protect would be happening well outside
the window in which the model reasons sharply.

**Progress becomes two numbers, and both are needed.** Tests delivered of total
scenarios is the number the customer is owed. Rows reviewed of total distinct
stays, because it is the anti-stall signal — a measured run once read step
definitions for 118 tool calls and wrote nothing — and because it is what
explains why the third Conversion took an hour and the three-hundredth took four
minutes.

ADR-0005 is unaffected. Checks still live in the stage that produces the work;
that stage is now a step inside a Conversion rather than a Phase.
