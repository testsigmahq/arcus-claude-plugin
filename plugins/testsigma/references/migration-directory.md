# The Migration Directory

Where a Migration keeps its state: `.testsigma/migration/`, inside the source
suite's own folder (ADR-0002). The source repository versions it, so a Migration's
state travels with the code it describes rather than depending on a directory
nobody tracks.

This file is the single definition of what lives there. A skill that writes to the
Migration Directory points here rather than restating the list, so the seven files
cannot drift apart across the skills that share them.

One file per concern. Not one state file, because a person reviews these and they
land in the source repository's diffs, where a single churning file is unreadable.

## The files

**`migration.md`** — the marker. What this Migration is: when it started, which
Source Adapter was chosen and why, the source snapshot it is pinned to, the CLI
build in use and the checks that build supports, and the enumeration summary
(total step lines, distinct Source Steps, Collapse Ratio, singletons, and the
parameterisation profile). Written once by survey and amended only when one of
those facts changes.

**`step-map.md`** — the reviewed mapping from every Source Step to its expression.
The largest artifact and the one most read, so it is a table. A row carries the
source text, its occurrence count, its parameter shapes, the proposed expression,
and a status. One Source Step may map to several steps.

**`open-questions.md`** — questions put to the Operator that have not been
answered. Added to at the moment a question arises, and cleared only by an answer.
This file exists because the alternative was demonstrated: a question was asked
once, never answered, and nothing anywhere recorded that it was still open.

**`platform-facts.md`** — things learned about Testsigma's own authoring surface
that no reading of a source could reveal. The Migration settles these itself, by
probing, rather than asking the Operator.

**`application-facts.md`** — things true of the application under test. Only a
person who knows that application can answer one, so each stays open until
answered. Kept apart from Platform Facts because who can answer them is the
distinction that matters.

**`residue.md`** — the Source Steps the Migration could not express, each with a
stated cause and the reasoning that produced it. An unexpressible step and an
unresolved element are distinct causes. No entry is final: a cause is overturned
when the format gains a spelling, or when one is found that nobody had used.

**`check-record.md`** — which checks ran against which Unit of Work. A check that
could not run is recorded as not checked, never as a pass. When the CLI gains a
check it did not have, the Units converted before it are marked as not checked
against that capability rather than inheriting a pass they never earned.

## Skeletons

Survey creates all seven. Six of them start empty, and they are created anyway so
that a later session finds the same shape every time and does not invent one. Write
these exactly; a Migration's files are read by several skills and by a person.

`migration.md`:

```markdown
# Migration: <suite name>

Started: <date>
Source snapshot: <commit> on <branch, or "detached HEAD">
Source adapter: <name> — <why this one>
  hides-sequence: <value>  carries-locators: <value>  value-language: <value>

## CLI build
Program: <resolved path>
Build: <commit of the checkout, or the version if it reports one>
Probed: <date>
Checks available: <the commands and flags the help listed>

## Enumeration
Total source steps: <n>
Distinct Source Steps: <n>
Collapse Ratio: <n>
Occurring exactly once: <n>
Parameterisation: <n> unparameterised, <n> single-valued, <n> genuinely varying
```

`step-map.md`:

```markdown
# Step Map

| Source Step | Occurrences | Parameter shapes | Expression | Status |
|---|---|---|---|---|
```

`open-questions.md`:

```markdown
# Open questions

Each stays here until it is answered. Nothing else clears one.

| Raised | Question | Asked of | Answer |
|---|---|---|---|
```

`platform-facts.md`:

```markdown
# Platform facts

True of Testsigma's authoring surface. Settled by probing, not by asking.

| Established | Fact | How it was established |
|---|---|---|
```

`application-facts.md`:

```markdown
# Application facts

True of the application under test. Only someone who knows it can answer.

| Raised | Fact needed | Answer | Answered by |
|---|---|---|---|
```

`residue.md`:

```markdown
# Residue

Not final. A cause is overturned when a spelling is found or the format gains one.

| Source Step | Cause | Reasoning | Revisit when |
|---|---|---|---|
```

`check-record.md`:

```markdown
# Check record

"not covered" is not a pass.

| Unit of Work | Kind | Checks run | Not covered | Under CLI build |
|---|---|---|---|---|
```

## Rules that hold across all of them

A Migration Directory is created by survey and never by hand. If one already
exists, the Migration has already started, and the right move is to resume rather
than to start again.

Nothing in here is generated from the source on demand. Every file is a record of
a decision or an observation that cost something to make, which is why it is
versioned alongside the code it describes.
