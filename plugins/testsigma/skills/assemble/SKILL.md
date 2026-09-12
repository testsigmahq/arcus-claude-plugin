---
name: assemble
description: Use when building Testsigma tests from a Migration's reviewed Step Map rows — assembling scenarios, converting a feature file whose rows are already reviewed, or checking assembled tests for document order and block nesting. Not the way into a Migration — where nothing has been surveyed or mapped yet, survey and map come first. Builds only from reviewed rows, stands an empty marker block where a residue row falls so a declined step is never silently absent, refuses a test that references an unresolved element, and checks every finished test for the order fault that compiles, passes preflight and survives a round trip.
---

# Assemble: build tests from reviewed rows

Assembly turns reviewed Step Map rows into Testsigma tests. It does no mapping:
every decision about what a Source Step means was made and reviewed in the
mapping stage, and reopening one here would mean deciding it twice, differently.

This stage owns the document-order and block-nesting check. By ADR-0005 that
check has no skill of its own; it is the exit condition of this one.

**Who you are talking to.** The person running a Migration is the Operator. They
know Testsigma and do not necessarily read code, so nothing you put in front of them
carries code, a file path, a stack trace or a diagnostic code. Those go in the
Migration Directory. They are copied here rather than pointed at because a
question arises mid-work; `${CLAUDE_PLUGIN_ROOT}/references/asking.md` decides
them and covers everything else shown to the Operator. See
`${CLAUDE_PLUGIN_ROOT}/CONTEXT.md` for the vocabulary this plugin uses with them.

The files this reads and writes are defined in
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`.

## Before anything: mapping must have produced something

If `.testsigma/migration/` is absent, survey has not run and there is nothing to
assemble. Stop. If it exists but `step-map.md` holds no reviewed rows, mapping
has not produced anything yet; say so and run mapping rather than assembling
from proposals.

## Step 1: Build only from reviewed rows

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

A `residue` row is the exception and does not block its scenario. It is a decided
row — decided as inexpressible — so it is assembled, as a marker. The next step
says how. Treating `residue` as "not `reviewed`, therefore skip" is the reading
that drops the step, and it is the natural reading of the rule above, which is
why it is written out here.

## Step 2: Refuse a test that references an unresolved element

Read `residue.md`. It is keyed by Source Step and element, so an unresolved
element names the parameter value that identifies it rather than blocking a
whole row. Refuse to assemble any test that references an element recorded there
as unresolved.

Why refusing beats standing in something is stated once, in
`${CLAUDE_PLUGIN_ROOT}/references/element-resolution.md`,
which owns what an unresolved element makes of a test. Read it there. It is the
reason this step is a refusal rather than a warning, and it is not restated here
because a safety rule kept in two places is one that softens in one of them.

A row whose other elements all resolved is not blocked. Decide per element, at
the parameter value, which is what that column is for.

## Step 3: A residue row becomes a marker, not a silence

Every `residue` row that a scenario uses is assembled as the source step's own
block, in the position the step would have occupied, with an empty body and the
need named in its label. A block never contains another block, so a partly
converted step carries its remainder the same way — in the label — rather than
in a nested marker.

This is the difference between Residue and a Divergence, and it is decided here
rather than in mapping. A step recorded as Residue and then left out of the test
is a test that reads as complete and is not — which is the definition of a
Divergence in `${CLAUDE_PLUGIN_ROOT}/CONTEXT.md`. The Migration Directory knowing
about the gap does not repair that, because the person who runs the test and the
person who reads `residue.md` are not the same person and often not the same
week.

How the marker is written, and what its label must carry, are in
`${CLAUDE_PLUGIN_ROOT}/references/authoring.md`. The short of it: the label names
what was needed, not that something is missing.

Then write the per-test document, `residue/<test>.md`, one per assembled test,
with a row for each marker in it. Its shape is in
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`. Write it as the test
is assembled and not in a sweep afterwards — a sweep re-derives from the file
what was already known while writing it, and re-derivation is where the label and
the entry drift apart.

A test carrying markers is still assembled and still checked. It is not refused,
and it is not reported as done without qualification: report it as assembled with
*n* markers, so the count is visible beside the test rather than only in a
document nobody opened.

## Step 4: Build the test

The rules the validator and the push enforce — which templates a new step may
use, how environment names and layout must be written, what to do after the first
push of a new entity kind, and how to mark a region left unconverted on purpose —
are in `${CLAUDE_PLUGIN_ROOT}/references/authoring.md`. Follow it;
most of those constraints only surface at push time, and by then the work is done.

**One block per source step, labelled with that step's text.** Express the row
inside it — where a row maps one Source Step to several Testsigma steps, emit
all of them inside that block, in the row's order.

The envelope is not decoration. It is what makes the next step's comparison
possible: a test written as bare statements can be compared with nothing, so
whether it covers its scenario is unanswerable and therefore unasked. It is also
what a reviewer reads, since the source step's own words are the only name that
survives from one side to the other.

Nest blocks as the source nests them. In a `.sigma` working copy the document
order is the lexical order and parentage is the lexical nesting, so a correctly
written file is correct by construction — which is why the fault the next step
looks for is not visible here.

**Build in slices of about fifteen source steps.** After each slice: `validate`,
coverage for the slice, then commit —

    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_coverage.py \
      --steps <the scenario's steps> --through <steps done so far> <the test>

A failing slice is finished before the next begins; push once at the end. Why,
in `${CLAUDE_PLUGIN_ROOT}/references/checks.md`.

## Step 5: Check that every source step is accounted for

Run `${CLAUDE_PLUGIN_ROOT}/scripts/check_coverage.py --steps <steps> <test>`,
passing the scenario's steps one per line — the ones already read while mapping.
It reports how many are accounted for and names every one that is not.

A step is accounted for when a block claims it, whether that block holds the
converted steps or stands empty as a marker. Nothing else counts, and a test
with an unaccounted step is not assembled.

This is the check that catches a conversion stopping early, and no other check
can. Validity looks at what is in the file. The order check looks at how it is
arranged. The element sweep finds a dropped step only when it left an element
behind. All three ask whether the file is right; this one asks whether it is all
there, which is a different question and needs the source to answer.

Measured: a run converted the nine API steps at the head of a fifty-five step
scenario, stopped, and reported "all 7 steps (pure API, no UI)". The file
compiled, the tenant took it, `pull` said no difference, and `residue.md` was
empty. Every signal said done. The step count was the only thing that disagreed,
and nothing was reading it.

Report coverage as *n of m* beside the test, always — including when they match.
A number that is only printed when it is wrong is one nobody learns to look for.

## Step 6: Check document order and block nesting

This is the exit condition of this stage. A test is not assembled until it has
passed this check, and a test that has not been checked is not done.

Run `${CLAUDE_PLUGIN_ROOT}/scripts/check_step_order.py`. Given a working copy it
derives the correct order; given the order numbers the platform reports, it
checks them and names every step out of place.

What the property is, why an id is not the order, why the plugin computes it
rather than asking the CLI, and why running the test cannot replace it, are in
`${CLAUDE_PLUGIN_ROOT}/references/checks.md` under *where a step sits among its
siblings*.

## Step 7: Check every param against the profile its test declares

Run `${CLAUDE_PLUGIN_ROOT}/scripts/check_profile_refs.py <workspace>`.

`validate` pools every profile's columns and checks the pool, so a reference to
another profile's column compiles. At run time nothing substitutes, the step
reads the marker as literal text, and the test passes having checked nothing —
a green test that tests nothing is worse than a failing one, because nobody
looks at it again.

Tests declaring no profile are skipped, and that is deliberate rather than a
limitation; `authoring.md` says why.

## Step 8: Sweep for elements nothing references

Cheap, and it earns its place — as a secondary check. The primary one is
call-chain coverage during mapping, and the difference is measured: in the
conversion this plugin came from, three separate element audits found one defect
between them and produced two false positives, while composites converted partway
accounted for six. Run this sweep, and do not mistake it for the check that finds
missing work.

After assembling, list every element the Migration has created or reused and find
the ones no step refers to.

An element that was lifted from the source but is referenced by nothing usually
means a **dropped step**: the reading found the element, and the step that used it
never got written. In the conversion this plugin was built from, a sweep of every
element in the workspace found exactly two unreferenced, and one of them was
precisely that — the locator had been lifted, with the right target, and the step
verifying the page was simply absent. Nothing else in the test pointed at the gap.

Report each one and say which it is. An element belonging to a scenario nobody has
converted yet is benign and stays. An element belonging to a scenario that was
converted is a missing step, and the row it came from goes back to `unreviewed`.

Two unreferenced out of forty-two is also the finding that the omission was
isolated rather than systematic, which is worth reporting: it tells the Operator
whether to re-examine one test or all of them. Report the ratio, and re-derive the
total rather than quoting an earlier one — in the measured pass that total was
itself wrong by four for a dozen steps before anyone recounted.

**The sweep only finds a dropped step that left an element behind.** A step that
captured a value rather than touching the screen — storing a window handle, or a
identifier for a later step to read — leaves nothing for this to notice. Those are
caught by the comparison in mapping or not at all, so do not report a clean sweep
as evidence that no step was dropped.

## Step 9: Report what is out of place

When the check fails, report which steps are out of place and the window each
one had to fall inside. A report saying only that a test is wrong cannot be acted
on, and the specific step is what makes the difference between a fix and a
re-examination of everything.

Do not assemble the test as done and note the failure beside it. It is not done.

A step for which no order was reported is recorded as not checked, never as a
pass. An unchecked step reading as clean is the failure mode ADR-0001 exists to
prevent: three checks that cannot see the fault class are worse than none,
because they read as reassurance.

## Step 10: Record the check and commit

Write what ran into `check-record.md`, per test, naming the CLI build in use.
The five checks, the order they run in, and what a check that could not run is
recorded as are defined in
`${CLAUDE_PLUGIN_ROOT}/references/checks.md`. Follow it rather than
deciding here what counts as checked.

Run `${CLAUDE_PLUGIN_ROOT}/scripts/check_stage.py` over the assembled test
first — it is check 3 over every block at once, and what it reports is part of
the record.

Commit the Migration Directory *and the assembled working copy* as tests are
built — scoping the commit to the Migration Directory leaves the .sigma files
behind, which is half the state. Then run
`${CLAUDE_PLUGIN_ROOT}/scripts/check_committed.py --suite <the suite>` before the stage ends and
commit what it lists.
Put anything unresolved where it belongs before finishing: a question for the
Operator into `open-questions.md`, something learned about Testsigma into
`platform-facts.md`, something only they can answer about their application into
`application-facts.md`.

Then report progress in tests: how many are assembled and checked, how many are
waiting on an unreviewed row, and how many are refused for an unresolved
element.
