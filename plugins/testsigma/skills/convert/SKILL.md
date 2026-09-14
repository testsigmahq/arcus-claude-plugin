---
name: convert
description: Use when a surveyed Migration should deliver its next Testsigma test — converting the next scenario, converting a named scenario, or continuing a Migration whose survey is done. Not the way into a Migration, and not a way to convert a suite in bulk — survey comes first, and this performs exactly one Conversion and stops. Picks the next scenario by the unseen Source Steps it introduces, maps the steps it reaches, resolves their elements, assembles and checks the test, records the row versions it consumed, commits, and reports tests delivered of total scenarios.
---

# Convert: one scenario, end to end

A Conversion is the end-to-end work on one source scenario: map the Source Steps
it reaches, resolve the elements those steps name, assemble the test, check it,
record it, commit it. Then stop.

This is how a Migration delivers (ADR-0012). The Operator gets a working test on
the first day rather than in the third week, and a delivered count that rises
from then on. The Step Map is shared and fills as Conversions accumulate, so a
Source Step decided in one is free in every one after it — the economics that
made mapping worth doing are untouched, and only the order changes.

**Who you are talking to.** The person running a Migration is the Operator. They
know Testsigma and do not necessarily read code, so nothing you put in front of
them carries code, a file path, a stack trace or a diagnostic code. Those go in
the Migration Directory. They are copied here rather than pointed at because a
question arises mid-work; `${CLAUDE_PLUGIN_ROOT}/references/asking.md` decides
them and covers everything else shown to the Operator. See
`${CLAUDE_PLUGIN_ROOT}/CONTEXT.md` for the vocabulary this plugin uses with them.

The files this reads and writes are defined in
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`.

## One Conversion per invocation, and then stop

**Perform exactly one Conversion and end the session's work.** Do not take the
next scenario, and do not offer to. When the report is delivered, this is over.

The rule is binding rather than a preference, and the reason is measured. A loop
accumulates every scenario's source reading in one context window: by the tenth
scenario the call-chain expansions, helper bodies and locator hunts of nine
others are still in front of the judgement calls this plugin exists to protect,
and those calls are then being made well outside the window in which a model
reasons sharply. The fault classes catalogued in
`${CLAUDE_PLUGIN_ROOT}/references/fault-classes.md#where-to-start-for-the-row-in-hand`
are judgements failing quietly rather than mechanisms breaking loudly, so nothing
downstream would catch one.

One per invocation also means every session starts from the Migration Directory
and nothing else, which is what the directory was built for. A Conversion that
needed the previous session's context would have made the directory a decoration.

## Before anything: a Migration must have been surveyed

If `.testsigma/migration/` is absent, survey has not run. Stop, and say that the
suite has not been surveyed yet, so there is no adapter chosen, no snapshot
pinned and no queue of scenarios to convert. Run survey.

If it is present, read it before working. `migration.md` names the adapter, the
pinned snapshot and where the working copy goes; `scenarios.md` is the queue;
`step-map.md` holds what has already been decided.

## Parking: when only the Operator can answer

**Where a Conversion needs something only the Operator can supply, park it rather
than stopping.** Something only the Operator can supply is a question about their
application that nothing in the source or the target project answers, or an
element the source does not carry, the target project does not hold and only they
can capture. Before Conversions, one such question could hold up an entire
Migration; for a customer onboarding onto Testsigma that is weeks of silence
traceable to a single question nobody chased, and it is the failure parking exists
to prevent.

To park it: set the scenario's status in `scenarios.md` to `parked`, and write in
`Reason` what it waits on, in one line. Put the question itself in
`open-questions.md` as well, because `Reason` says what is outstanding and
`open-questions.md` is where the Operator answers it.

`Reason` is read back to the Operator by `resume`, so it is written in their
terms and under the rule above, like everything else put in front of them.
"Waiting on which of the two Submit controls on the checkout screen is the live
one" is a Reason; a locator is not.

**Having parked, this invocation ends.** Do not go on to another Conversion in the
same window. Parking is not a way around one Conversion per invocation: the loop
takes the next one in the next invocation, which is how a Migration keeps moving
without a session's judgement calls piling up behind one another.

A parked scenario becomes selectable again as soon as the thing it waited on has
cleared, by returning to `pending` in Step 1. It then goes through the same loop
as any other Conversion, from the top — mapped, resolved, assembled, checked,
recorded. There is one path to a delivered test, not a second one for scenarios
that were once parked.

**Residue never parks a Conversion.** A Source Step the format cannot express is
a decided outcome rather than an outstanding one, and it assembles as its marker
so the step is never silently absent. Losing a whole test to a step that was
correctly declined would be a regression.

The two are told apart by who is owed something. Parking waits on the Operator and
names what for; Residue waits on nobody, because someone has already ruled. An
element the source does not carry is one or the other by the same test: parked
while the Operator has yet to capture it, Residue once the ruling is that it cannot
be had.

## Step 1: Take the next scenario

Before selecting, look at the parked rows in `scenarios.md`. Where what a row
waits on has cleared — the Operator has answered the open question, or the element
it needed is now available — set that scenario back to `pending` so the ordering
can reach it. A parked scenario nothing returns to `pending` is a scenario the
Operator unblocked and the Migration forgot.

Run `${CLAUDE_PLUGIN_ROOT}/scripts/next_conversion.py --suite <the suite>`. It
names the pending scenario introducing the most Source Steps nobody has judged
yet, and that is the scenario this Conversion converts.

The choice is a script rather than a judgement so that two sessions reading the
same Migration Directory choose the same scenario. Do not re-derive it, and do
not override it because another scenario looks more interesting.

The one thing that does override it is the Operator naming a scenario. Once the
script reports that vocabulary has saturated, ordering has handed over to their
priority — tell them so, and convert what they ask for.

## Step 2: Map the Source Steps this scenario reaches

Use the `map` skill, scoped to this scenario. Its Step 0 already expands call
chains one scenario at a time, which is exactly this.

Rows the Step Map already holds as `reviewed` or `adopted` are reused as they
stand. That reuse is the whole economics of mapping, and it is why the third
Conversion takes an hour and the three-hundredth takes minutes.

**Every row this Conversion decides gets the same reading it would have got
before.** The helper behind the line is opened, and the proposed expression is
compared against what that helper actually does, before the row may be called
reviewed. Delivering sooner weakens no check: a row is trusted forever once it
says `reviewed`, and two measured defects were rows that were wrong from the
start and then reused thirty-five times.

A row whose Expression or Status changes gets its `Version` bumped, per the
Migration Directory reference. Occurrence counts and provenance change every
Conversion and never bump it.

## Step 3: Resolve the elements those steps name

Where the adapter declares `carries-locators: yes`, the source answers this in
the same reading that recovered the sequence, and there is nothing separate to
do.

Where it does not, use the `resolve-elements` skill, scoped to the elements this
scenario needs. It looks in the source, then in the target project, and only then
asks the Operator — and when it asks, it asks for a whole screen at once, because
capture costs them a visit per screen whether they are asked for one element or
twelve.

## Step 4: Assemble the test and check it

Use the `assemble` skill for this one scenario. It builds only from decided rows,
stands a marker block where a residue row falls, refuses a test referencing an
unresolved element, and runs the checks in the order
`${CLAUDE_PLUGIN_ROOT}/references/checks.md` fixes.

Do not restate or shortcut any of that here. A Residue row assembles as its
marker and does not stop the Conversion: a step the format cannot express costs
that step, never the whole test.

## Step 5: Record what this Conversion consumed, and commit

Write the `assembled.md` row: the scenario, the test, the row versions it
consumed, and when. The versions are the point — a test whose recorded version
is behind the row's current one was built on a decision since overturned, and
this row is what makes that findable without reading the whole working copy.

Set the scenario's status in `scenarios.md` to `done`.

Commit the Migration Directory **and the assembled working copy** together, as
the Conversion ends. Scoping the commit to the Migration Directory leaves the
`.sigma` file behind, which is half of what was just produced. Run
`${CLAUDE_PLUGIN_ROOT}/scripts/check_committed.py --suite <the suite>` and commit
what it lists.

Committing per Conversion is what makes a session that ends early lose nothing.

## Step 6: Report, and stop

Tell the Operator, in this order:

- the test delivered, by the scenario's name
- **tests delivered of total scenarios** — the onboarding number, and the one the
  customer counts
- rows reviewed of total distinct — the anti-stall signal, and what shows a
  Migration reading source and writing nothing
- how many rows this Conversion decided new versus reused — this is what explains
  why the third Conversion took an hour and the three-hundredth took minutes
- any Concession or Residue recorded, and what each one costs in practice
- whether anything parked, and what it waits on — the one part of the report the
  Operator alone can act on

Then stop. Anything unresolved goes where it belongs first: a question for the
Operator into `open-questions.md`, something learned about Testsigma into
`platform-facts.md`, something only they can answer about their application into
`application-facts.md`. A question that exists only in this session's transcript
is a question that will be lost.
