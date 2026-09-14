---
name: map
description: Use when mapping a surveyed suite's Source Steps into Testsigma expressions — building or continuing the Step Map, deciding how a Gherkin phrasing or Tosca module should be expressed, or working through unreviewed rows. Opens the helper behind each source line to recover what it really does, compares every proposed expression against that implementation before a row can be called reviewed, and resolves the elements each row needs from the source itself where the source carries them, and records anything the format cannot express as Residue with its cause.
---

# Map: build the Step Map

Mapping decides, once per distinct Source Step, how that step is expressed in
Testsigma. Every occurrence of that step then reuses the decision, which is why
the cost of a Migration scales with a suite's vocabulary rather than its line
count.

This stage owns the check that matters most. Four of the six known faults in the
conversion that produced this plugin were a source line hiding a helper that did
something else, and comparing against the implementation is the only thing that
found them. By ADR-0005 that check has no skill of its own: it is the exit
condition of this one.

**Who you are talking to.** The person running a Migration is the Operator. They
know Testsigma and do not necessarily read code, so nothing you put in front of them
carries code, a file path, a stack trace or a diagnostic code. Those go in the
Migration Directory. They are copied here rather than pointed at because a
question arises mid-work; `${CLAUDE_PLUGIN_ROOT}/references/asking.md` decides
them and covers everything else shown to the Operator. See
`${CLAUDE_PLUGIN_ROOT}/CONTEXT.md` for the vocabulary this plugin uses with them.

The files this reads and writes are defined in
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`.

## Before anything: there must be a Migration to map into

If `.testsigma/migration/` is absent, survey has not run. Stop. There is no
adapter chosen, no snapshot pinned and no Step Map to write rows into, and
mapping without those produces rows nobody can trace back to a source.

If it is present, read it before working. `migration.md` names the adapter and
the pinned snapshot; `step-map.md` holds the rows already decided. Where you need
the state in full, read the rest of the Migration Directory files rather than
reaching for the Operator's own command.

## Step 0: Resolve everything before authoring anything

The order of this stage is measured, not a preference. Of two conversions of
comparable size, the one that authored each row and audited afterwards produced
twenty-one defects, every one found after the target code existed; the one that
resolved first and authored second produced five, four caught before any target
code was written.

Read the `Conducting the comparison` part of
`${CLAUDE_PLUGIN_ROOT}/references/fault-classes.md#conducting-the-comparison`
once here, before any row exists. It is what a verdict rests on, what a script
may be trusted with, and how a finding is recorded — rules about the stage
rather than things to look for in a row, so reading them per row is both too
often and, where a row's text does not mention them, never.

Then do two things across the whole scenario **before proposing any expression**.

**Expand every call chain**: resolve each step definition and follow every call it
makes, transitively, to the leaves. That yields the complete list of actions the
scenario performs, and it exists before there is anything to compare against.

**Inventory the elements, bound to their call sites**: every element the expanded
chains actually reach, taken from the class the chain reaches rather than from
anywhere in the source declaring that name, each name checked for uniqueness
across the workspace.

Those two passes caught three wrong-class locators and a format-string trap before
authoring — the two categories that cost the audited conversion the most. The
per-row comparison below still gates each row; this is what makes it cheap.

## Step 1: Fill one seeded row at a time

Survey seeded `step-map.md` with every distinct Source Step, `unreviewed`. Work
those rows, not the suite's lines. Each is one Unit of Work, carries its
occurrence count from survey, and is decided once.

**Write the row before opening the next one.** A row is not decided until it is
written down: reading produces nothing until it lands in one, so a session
holding twenty resolved steps in its head has twenty units of work that do not
exist yet, and loses all of them if it ends. The seeded row makes the alternative
cheap — it is already there, and finishing it is an edit.

Not in a batch at the end, and not via a generated script that rewrites the
whole table — one run lost every row to a syntax error in exactly that.

Reuse the verdict at every occurrence. A step decided here is not revisited when
it appears again, in another feature file or scenario; that reuse is the entire
economics of mapping.

**One exception: when a new scenario first uses a row decided for another, the
call-chain check runs again** (`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`).

Order by occurrence count, highest first: an early wrong verdict on a frequent
step is the most expensive mistake available. Then the steps that genuinely vary,
which carry most of the judgement. Singletons amortise nothing and can wait, but
none can be skipped.

## Step 2: What a row carries

The row's columns are defined in
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`. They exist so that
reviewing a row does not mean going back to the source, which is the difference
between a review that happens and one that is deferred.

Two things about a row are this stage's rather than the schema's. **One Source
Step may map to several Testsigma steps.** A source line that really
performs three actions is expressed as three, and forcing it into one is how a
Composite Step becomes a converted test. The row holds the whole sequence.

A status is `unreviewed`, `reviewed` or `residue`, as defined in the Migration
Directory reference. A row is `unreviewed` from the moment it is written.

### Before a row is proposed: the slot decides the value

Naming the right verb does not make a row legal: a slot declares which **value
kinds** it will hold, and the kinds, and how to ask the build what a slot
accepts, are in `${CLAUDE_PLUGIN_ROOT}/references/authoring.md`. Never settle a
mismatch with a raw literal — freezing a generated or captured value into a
constant passes every check and is a Divergence. Where a row's value is not a
raw literal, record a `Kind:` line in its Expression cell, as
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md` defines.

## Step 3: Open the helper behind the line and read its sequence

The source line does not tell you what the step does. Open the helper it names,
every time, for every distinct Source Step, and read it for sequence. Work
against the implementation rather than the surface syntax: the surface is what
was already trusted on the conversion that produced this plugin, and it was
wrong four times out of six.

The adapter's own Sequence section states where the sequence lives for this
format and which traps recur in it. Follow it. Four shapes recur across every
source format met so far, all four producing a test that runs and passes:
`${CLAUDE_PLUGIN_ROOT}/references/fault-classes.md#four-shapes-a-helper-takes-and-three-of-them-read-as-one-action`.

One of the four is an instruction rather than a description, so it is here:
**treat every helper whose name contains `wait`, `until`, `refresh` or `poll` as
a loop until the source shows otherwise**, including the shape that reads as an
assertion, which is where the volume is.

Report what the helper actually does, in the Operator's terms, whenever it
differs from what the line implies. A difference found and not said reaches the
converted suite.

**Ask the locator question in this same reading.** Where the source carries
locators they are in the same file you have just opened for sequence, so it is
one reading with two questions rather than two readings. Lift the locators as
they are declared; do not reinvent them. The adapter's Locators section says
where they live in this format.

**Read it yourself.** Breadth may be delegated; this reading may not. What comes
back from a delegated reading is a summary, and a summary of a helper is the
surface again. Where one already exists, open the file rather than ask for a
fuller one — `fault-classes.md#a-verdict-given-without-the-implementation`.

Separating the two readings is the fault, not an inefficiency — see
`fault-classes.md#a-verdict-given-without-the-implementation` for the pass that
opened every page object, read it for locators, and never asked what the code
did.

## Step 4: Ask whether the project already expresses this step

Where `.testsigma/migration/existing/` holds an inventory, look there before
deciding an expression. A step group the team already wrote is the cheapest
correct answer and the one a person can be asked about.

Adopting is not free and never bulk: the pulled entity is verified against the
same call chain an authored row is, and a disagreement goes to the Operator as an
open question rather than being repaired. `${CLAUDE_PLUGIN_ROOT}/references/adoption.md`
holds the procedure, the `Adopted:` line a row records, and why a row that could
not be verified says so.

## Step 5: Resolve the elements a row references

This step runs here only where the adapter declares `carries-locators: yes` or
`sometimes`. Where it declares `no`, the resolve-elements skill takes them from
the target project or the Operator, inside this same Conversion.

The procedure — the three places to look, in order, and what happens when none of
them answers — is defined in
`${CLAUDE_PLUGIN_ROOT}/references/element-resolution.md`, which the
resolve-elements skill shares.

## Step 6: Compare the expression against the source before finishing

The comparison is the exit condition of this stage. A row cannot be marked
reviewed before its proposed expression has been compared against the helper's
implementation — not when the count is large, not when the step looks obvious,
and not when the session is ending. A row that has not been compared stays
`unreviewed`, which is what the status is for.

It sits third in the check order and is not replaceable by running anything —
every fault in this class produces a test that runs and passes while testing
something weaker. `${CLAUDE_PLUGIN_ROOT}/references/checks.md` holds the order and
the measurement behind it.

**Start with coverage of the call chain, because that is where the defects were.**
Enumerate every call the step definition makes, transitively through the helpers it
delegates to, and require each to map to at least one step in the expression.
Report the calls that map to none.

Run it, do not only read it: record the implementing method in the row's
`Source` column and run the call-chain check in
`${CLAUDE_PLUGIN_ROOT}/references/checks.md`. A composite converted partway was the largest
single class of defect in the conversion this plugin came from, and it produces a
row that reads correctly and is simply short. The same walk settles which locator
each step reaches, which is the only thing that catches an element lifted from the
wrong place in a source that genuinely contains it.

Compare on three points: whether the expression performs the same actions in the
same order, whether it asserts the same thing, and whether anything the helper
does is missing from it or invented in it.

The other fault classes are catalogued in
`${CLAUDE_PLUGIN_ROOT}/references/fault-classes.md#where-to-start-for-the-row-in-hand`;
work through its first part for every row rather than trusting recall of it. A
loose comparison in the source is a question rather than a licence — both are
stated in `${CLAUDE_PLUGIN_ROOT}/references/checks.md`.

## Step 7: Concessions, for what the format expresses differently

Most differences are neither a clean expression nor a refusal. The format has no
verb for what the source did, the nearest spelling differs in a way you can
state, and taking it is the right call. That is a **Concession**, and it is
recorded rather than smoothed over.

Record it in the Step Map row's Expression cell, on its own line, beginning
`Concession:` and then what the source did, what the expression does instead, and
when the difference would matter. The prefix is fixed so that resume can count
and list them; the reference defines it. The
platform limit that forced it goes in `platform-facts.md` — "no element-scoped
Enter verb exists", "no presence verb is available in a condition" — because that
limit is a fact about Testsigma that the next row will need and that probing, not
asking, settles.

The measured case: the source tested whether an element was absent, and the
format offers no presence check inside a condition — only enabled, disabled,
visible and not visible. The row used "not visible", which differs exactly when
an element is present but hidden, and said so.

A Concession is expressed work and does not block assembly; Residue is declined
work and does. `${CLAUDE_PLUGIN_ROOT}/CONTEXT.md` carries what separates the two
from a Divergence, and it is worth reading before deciding a row is one rather
than another.

## Step 8: Residue, for what the format cannot express

When a Source Step cannot be expressed, record it in `residue.md` with a stated
cause and the reasoning that produced the ruling. An unexpressible step and an
unresolved element are distinct causes and are never merged.

Record its **Standing** too, `gap` or `refusal`. Where you cannot tell, write
`gap`, because that is the reading that gets looked at again.

The **Cause** is one of a fixed set, not prose;
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md` holds the set. Two of
them merge by accident: a **step addon** is wanted when no Verb performs the
action, a **data generator addon** when no generator produces a value. Both feel
identical while writing a step that will not finish, and they are requests to
different people, so decide which while recording the entry.

The reasoning is what lets a ruling be overturned later, so write the reasoning
and not just the verdict: one case already believed unexpressible turned out to
have a spelling that existed all along. What a Standing means, what an Addon is,
and why Residue is not a Divergence, are in `${CLAUDE_PLUGIN_ROOT}/CONTEXT.md`.

Set the row's status to `residue`. It is not a status assembly may skip over: a
`residue` row is assembled as a marker, per the stage that builds tests. Leaving
the row out of `step-map.md` entirely would lose that, and the step would go
missing from every test that used it.

## Step 9: Record and commit

Record the comparison in `check-record.md` as each row is reviewed. A reviewed row
is a Unit of Work that has been checked, and a record covering only assembled tests
would leave the stage with the strongest evidence of finding faults absent from it.
Name the CLI build it ran under; `${CLAUDE_PLUGIN_ROOT}/references/checks.md` says
what a check that could not run is recorded as.

Commit the Migration Directory as rows accumulate, and before the stage ends run
`${CLAUDE_PLUGIN_ROOT}/scripts/check_committed.py`, committing what it lists. Put
anything unresolved where it belongs before finishing: a question for the
Operator into `open-questions.md`, something learned about Testsigma into
`platform-facts.md`, something only they can answer about their application into
`application-facts.md`.

Then report progress in rows: how many distinct Source Steps are decided, how
many remain, and what the comparison found. Occurrence-weighted coverage is the
number that means something to the Operator, since decided rows carry their
occurrence counts with them.
