---
name: resolve-elements
description: Use when a Migration's source carries no locators — a Tosca subset export, an ALM design-step export, any source that describes what tests do but not how to find the controls — and the Step Map is mapped but its elements are unsatisfied. Runs as its own Phase after mapping, matching each element the Step Map names against the existing Testsigma project by name before asking the Operator to capture anything.
---

# Resolve elements

Some sources describe what a test does and nothing about how to find the things it
does it to. For those, the elements a Step Map names have to be satisfied from
somewhere other than the source, and that is a Phase of its own.

**This Phase runs only where the chosen adapter declares `carries-locators: no`.**
Where the adapter declares `yes` or `sometimes`, the locators sit in the same files
that carry sequence and resolution happens inside mapping, in one reading. Check the
adapter named in `migration.md` before doing anything here; running this Phase
against a source that carries locators means reading those files twice and asking
the Operator for what the code already said.

It runs after mapping, not before and not during. Mapping is what produces the list
of elements that actually need resolving, and resolving elements that no reviewed row
references is work spent on a guess.

**Who you are talking to.** The person running a Migration is the Operator.
They know Testsigma and do not necessarily read code, so nothing you put in front of
them carries code, a file path, a stack trace or a diagnostic code. Those go in the
Migration Directory. [../../references/asking.md](../../references/asking.md) is the
rule for what a question may contain; this does not restate it. See `CONTEXT.md` for
the vocabulary this plugin uses with them.

The files this reads and writes are defined in
[../../references/migration-directory.md](../../references/migration-directory.md).

## Step 1: Take the elements the Step Map names

Read `step-map.md` and collect every element its reviewed rows reference. That list,
and not the source, is the work of this Phase.

Count the distinct parameter values rather than the rows. A generic row that takes a
control and a screen as parameters names as many things to find as it has parameter
values, so the element count is not a proportion of the row count and an estimate
built from rows will be badly wrong.

Group them by screen before starting. An Operator asked for elements one at a time
across forty screens is being asked to navigate forty times; the same list grouped by
screen is one pass through the application.

## Step 2: Match the existing Testsigma project, by name

Before creating any screen or element, look for one already in the project that
matches by name, and reuse it. The Operator maintains those screens. A Migration that
duplicates them hands back a project with two of everything and no way to tell which
one is live.

Report what matched and what did not, as counts by screen. A match rate is the number
that tells the Operator how much of this Phase is left.

Where a name nearly matches, do not decide quietly. Say which existing element you
think is meant and let the Operator confirm, because a wrong reuse is worse than a
duplicate: it points a converted test at a control that was never the one the source
used.

## Step 3: Ask the Operator to capture what is left

Ask for a capture only when the existing project cannot supply the element, since
the source already cannot. Their time is the last resort and not the first.

Ask by screen, with the whole list for that screen at once, and say what each element
is for in the test's terms. A request to capture one control with no context is a
request the Operator has to reconstruct before they can act on it.

Record each capture in `platform-facts.md` as it is established, not at the end of
the Phase. This Phase can span sessions, and an element captured but unrecorded is a
capture the Operator will be asked for twice.

## Step 4: What nothing resolves becomes Residue

When neither the existing project nor the Operator can supply an element, record it
in `residue.md` as an unresolved element, naming the parameter value that identifies
it. That cause is distinct from an unexpressible step and the two are never merged.

An unresolved element blocks assembly of every test that references it. Never
substitute a placeholder and never assemble around it. A test that looks finished and
cannot run is worse than one that is visibly absent, because the absent test is on a
list and the placeholder is in a suite where it reads as coverage.

Record the block at the element's granularity, not the row's. A row whose other
elements all resolved is not blocked by one that did not.

## Step 5: Report and commit

**Write an `Element Resolution` section into `migration.md` when the Phase is
done** — every element matched, captured, or recorded as Residue — with the counts
below. That section's absence is how a later session knows this Phase is still open,
so a Phase finished without writing it reads as unfinished forever and `resume` will
keep naming it as the active Phase. It is the one signal that this Phase completed.

Commit the Migration Directory as elements resolve, scoped to that directory.

Report progress in elements: how many the Step Map names, how many were matched in
the existing project, how many the Operator captured, and how many are Residue.
Then say which tests are unblocked by this Phase, because that is the number that
tells the Operator what assembly can now do.
