---
name: assemble
description: Use when building Testsigma tests from a Migration's reviewed Step Map rows — assembling scenarios, converting a feature file's tests now that mapping is done, or checking assembled tests for document order and block nesting. Takes only reviewed rows, refuses a test that references an unresolved element, and checks every finished test for the order fault that compiles, passes preflight and survives a round trip.
---

# Assemble: build tests from reviewed rows

Assembly turns reviewed Step Map rows into Testsigma tests. It does no mapping:
every decision about what a Source Step means was made and reviewed in the
mapping stage, and reopening one here would mean deciding it twice, differently.

This stage owns the document-order and block-nesting check. By ADR-0005 that
check has no skill of its own; it is the exit condition of this one.

**Who you are talking to.** The person running a Migration is the Operator.
They know Testsigma and do not necessarily read code, so nothing you put in
front of them carries code, a file path, a stack trace or a diagnostic code.
Those go in the Migration Directory.
[../../references/asking.md](../../references/asking.md) is the rule for what a
question may contain; this does not restate it. See `CONTEXT.md` for the
vocabulary this plugin uses with them.

The files this reads and writes are defined in
[../../references/migration-directory.md](../../references/migration-directory.md).

## Before anything: mapping must have produced something

If `.testsigma/migration/` is absent, survey has not run and there is nothing to
assemble. Stop. If it exists but `step-map.md` holds no reviewed rows, mapping
has not produced anything yet; say so and run mapping rather than assembling
from proposals.

## Step 1: Take only reviewed rows

A row's status in `step-map.md` decides whether it may be used. Use rows whose
status is `reviewed`. Never assemble from a row that is `unreviewed`, and never
change a row's status from here — a status set by the stage that consumes the row
is not a review, it is a rubber stamp.

An `unreviewed` row means its expression has not been compared against the
source's implementation. Assembling it produces exactly the test the comparison
exists to prevent: one that runs, passes, and tests something weaker or
different.

Where a scenario needs a row that is not yet reviewed, leave that scenario
unassembled and say which row it is waiting on. A partially assembled suite with
a named gap is worth more than a complete one with an unreviewed step in it.

## Step 2: Refuse a test that references an unresolved element

Read `residue.md`. It is keyed by Source Step and element, so an unresolved
element names the parameter value that identifies it rather than blocking a
whole row. Refuse to assemble any test that references an element recorded there
as unresolved.

Refuse it; never substitute a placeholder and never assemble around it. A test
that looks finished and cannot run is worse than one that is visibly absent,
because the absent test is on a list and the placeholder is in a suite where it
will be read as coverage.

A row whose other elements all resolved is not blocked. Decide per element, at
the parameter value, which is what that column is for.

## Step 3: Build the test

Express each step from its reviewed row, in the source's own sequence. Where a
row maps one Source Step to several Testsigma steps, emit all of them, in the
row's order.

Nest blocks as the source nests them. In a `.sigma` working copy the document
order is the lexical order and parentage is the lexical nesting, so a correctly
written file is correct by construction — which is why the fault the next step
looks for is not visible here.

## Step 4: Check document order and block nesting

This is the exit condition of this stage. A test is not assembled until it has
passed this check, and a test that has not been checked is not done.

The check is a property of a whole test, not of a step, because it describes a
fault that only exists between steps. A conditional whose body is ordered outside
its own block draws empty and runs its steps late; no single step is wrong.

The property is arithmetic. For every step with a parent, the step's order falls
strictly between its parent's order and the order of the parent's next sibling,
with no upper bound where the parent has no next sibling. Siblings increase in
document order.

**An id is not the order.** An id is assigned when a step is created, so a step
authored later carries a higher id while sitting earlier in the document —
measured on a real conversion, a top-level step numbered 1718 preceded one
numbered 1604. Reading ids as order reports authoring history as a fault.

Run `${CLAUDE_PLUGIN_ROOT}/scripts/check_step_order.py`. Given a working copy it
derives the correct order; given the order numbers the platform reports, it
checks them and names every step out of place. The arithmetic lives there and is
not restated here, so there is one implementation of it.

**The plugin computes this itself rather than asking the CLI.** The check has to
hold whatever the installed build happens to verify, and this is the concrete
case behind ADR-0003: a fault class caught by eye became an automatic refusal in
the CLI inside about a day, and work converted before that had never been
checked for it. A check that depends on the build being new enough is a check
that silently was not run.

Running the test cannot replace this. The fault survives compilation, tenant
preflight and a full round trip: the round trip rebuilds the step tree from
parentage, and order is not parentage.

## Step 5: Report what is out of place

When the check fails, report which steps are out of place and the window each
one had to fall inside. A report saying only that a test is wrong cannot be acted
on, and the specific step is what makes the difference between a fix and a
re-examination of everything.

Do not assemble the test as done and note the failure beside it. It is not done.

A step for which no order was reported is recorded as not checked, never as a
pass. An unchecked step reading as clean is the failure mode ADR-0001 exists to
prevent: three checks that cannot see the fault class are worse than none,
because they read as reassurance.

## Step 6: Record the check and commit

Write what ran into `check-record.md`, per test, naming the CLI build in use.
The five checks, the order they run in, and what a check that could not run is
recorded as are defined in
[../../references/checks.md](../../references/checks.md). Follow it rather than
deciding here what counts as checked.

Commit the Migration Directory as tests are assembled, scoped to that directory.
Put anything unresolved where it belongs before finishing: a question for the
Operator into `open-questions.md`, something learned about Testsigma into
`platform-facts.md`, something only they can answer about their application into
`application-facts.md`.

Then report progress in tests: how many are assembled and checked, how many are
waiting on an unreviewed row, and how many are refused for an unresolved
element.
