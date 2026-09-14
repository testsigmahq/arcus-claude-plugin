---
name: resolve-elements
description: Use when a Conversion needs elements its source does not carry and its adapter already exists, declaring carries-locators no — a Tosca subset export, an ALM design-step export, any source that describes what tests do but not how to find the controls — and the rows this scenario reaches name controls nothing has satisfied yet. Called by convert and scoped to the screens one Conversion needs, matching each element against the existing Testsigma project by name before asking the Operator, and asking only for a whole screen at once.
---

# Resolve elements

Some sources describe what a test does and nothing about how to find the things it
does it to. For those, the elements a Step Map names have to be satisfied from
somewhere other than the source.

**This runs only where the chosen adapter declares `carries-locators: no`.**
Where the adapter declares `yes` or `sometimes`, the locators sit in the same files
that carry sequence and a Conversion has already resolved them inside mapping, in
one reading. Check the adapter named in `migration.md` before doing anything here;
running this against a source that carries locators means reading those files twice
and asking the Operator for what the code already said.

It runs after the mapping of the scenario in hand, not before and not during.
Mapping is what produces the list of elements that actually need resolving, and
resolving elements no reviewed row references is work spent on a guess.

**The procedure itself is not here.** Where an element comes from, in what order,
and what happens when nothing supplies it are defined in
`${CLAUDE_PLUGIN_ROOT}/references/element-resolution.md`.
This skill is the conduct around it: which elements to work on, how to put a
question to a person, and what to report.

**Who you are talking to.** The person running a Migration is the Operator. They
know Testsigma and do not necessarily read code, so nothing you put in front of them
carries code, a file path, a stack trace or a diagnostic code. Those go in the
Migration Directory. They are copied here rather than pointed at because a
question arises mid-work; `${CLAUDE_PLUGIN_ROOT}/references/asking.md` decides
them and covers everything else shown to the Operator. See
`${CLAUDE_PLUGIN_ROOT}/CONTEXT.md` for the vocabulary this plugin uses with them.

The files this reads and writes are defined in
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`.

## Step 1: Collect the elements this Conversion owes

Read `step-map.md` and collect the elements referenced by the rows this Conversion
reached — the scenario in hand, and no further — and note which screen each one
sits on. That list, and not the source, is what this Conversion owes. A suite-wide
sweep would resolve controls for scenarios nobody has mapped yet, which is a guess
dressed as progress and delays the test being built now.

Count the elements rather than the rows. A generic row taking a control and a screen
as parameters names as many things to find as it has parameter values, so an estimate
built from the row count will be badly wrong — the reference says how to count, and
the adapter's Locators section carries a measured example for the format in hand.

Group the list by screen before starting. An Operator asked for elements one at a
time across forty screens is being asked to navigate forty times; the same list
grouped by screen is one pass through the application.

## Step 2: Work the list, and conduct the asking

Follow the procedure in
`${CLAUDE_PLUGIN_ROOT}/references/element-resolution.md` for
each element. What this adds is how the parts involving a person are conducted.

**Where a name nearly matches, do not decide quietly.** Say which existing element
you think is meant and let the Operator confirm. A wrong reuse is worse than a
duplicate: it points a converted test at a control that was never the one the source
used, and it does it invisibly.

**Ask by screen, with that whole screen's list at once**, and say what each element
is for in the test's terms. Capture is cheap per screen and expensive per visit:
someone already looking at a screen captures eight controls nearly as fast as one,
so a single element that blocked a Conversion is never asked for alone. A request to
capture one control with no context is also a request the Operator has to
reconstruct before they can act on it.

**Record each capture in `platform-facts.md` as it is established**, not at the end.
A Conversion can end between the asking and the assembling, and an element captured
but unrecorded is a capture the Operator will be asked for twice.

Report what matched and what did not as counts by screen, as you go. A match rate is
the number that tells the Operator how much of this is left.

## Step 3: Report back to the Conversion

Report progress in elements: how many the rows in hand name, how many were matched
in the existing project, how many the Operator captured, and how many are Residue.

Where a screen's elements are still outstanding because only the Operator can
capture them, say so and stop. That is what parks the Conversion, and `convert`
owns what happens next — the scenario is parked with what it waits on, and the
Migration takes the next Conversion rather than stalling on this one.

Commit the Migration Directory as elements resolve, scoped to that directory. The
Conversion commits the working copy alongside it when it finishes.
