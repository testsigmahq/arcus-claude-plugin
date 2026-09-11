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

It gains an **Element Resolution** section when, and only when, a source with no
locators has had its elements resolved. Survey never writes it, so its absence is
how a later session knows that Phase is still open. Where the adapter carries
locators the section never appears, because there is no such Phase to finish.

**`step-map.md`** — the reviewed mapping from every Source Step to its expression.
The largest artifact and the one most read, so it is a table. A row carries the
source text, its occurrence count, its parameter shapes, the proposed expression,
and a status. One Source Step may map to several steps.

A row whose expression uses a value that does not come from the test itself
carries a **`Kind:`** line in its Expression cell, naming the Value Kinds it
uses — `Kind: runtime, function`. Rows using nothing but raw literals carry none,
because there is nothing about them to check. The prefix is fixed for the same
reason a Concession's is: a reviewer's question is "show me every row whose value
comes from somewhere else", and a fixed prefix is what makes that a sweep rather
than a reading. Whether the slot accepts that kind is established by asking the
build, per `authoring.md`.

A row whose expression differs from the source in a way that was judged and
accepted carries a **Concession** — see `CONTEXT.md` — and records it in the
Expression cell, on its own line, beginning `Concession:` and then what differs
and when it would matter. The marker is a fixed prefix rather than prose so that
concessions can be counted and listed: a Concession nobody can find is a
Divergence, which is the one thing the term exists to prevent. The platform limit
that forced it goes in `platform-facts.md`.

A row's status is one of `unreviewed`, `reviewed` or `residue`. A row is
`unreviewed` from the moment it is written until a person has looked at it;
nothing else may set it to `reviewed`. `residue` means the row has an entry in
`residue.md` and is not waiting on review. The vocabulary is fixed here because
resume counts the rows in each state and a private fourth value would be counted
as neither.

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

A Standing is `gap` or `refusal`, and it says which of the two kinds of stop this
is. A **gap** is a capability the format does not have yet, and the people who
own the format may be tracking it; a **refusal** is a construct declined on
purpose, and no build will bring it. Both stop a row, and only one is temporary.
Written together in one column they are re-read identically, which costs twice:
a settled decision gets re-examined every session, and a gap that has since
closed goes on looking permanent.

They differ in what revisits them, so `Revisit when` means something different
in each. A gap is revisited when the build changes — `cli-probe.md` says a build
that differs makes every capability possibly new, and a gap is the thing that
sentence is about. A refusal is revisited only when the Operator or the format's
owners reverse the decision, so it is not re-examined on a build change and
`Revisit when` names the decision rather than a version.

When neither is established, write `gap`. It is the reading that gets looked at
again, and the cost of being wrong about it is one re-examination rather than a
row written off for the life of the Migration.

An entry is keyed by Source Step **and element**, because the two causes do not
share a granularity. An unexpressible step blocks the whole row and leaves the
element column empty. An unresolved element blocks only the occurrences that name
that element, and the column carries the parameter value that identifies it — a
generic step's parameter values can far outnumber its rows, so marking the whole
row would block every occurrence that resolved perfectly well. Assembly reads
this column to decide which tests are blocked.

A **Cause** is one of a fixed set, not prose. Prose reads fine to whoever wrote
it and cannot be counted, sorted, or handed to the person who can close it:

| Cause | What is missing | Who closes it |
|---|---|---|
| `step addon` | no Verb in the Catalogue performs this action | whoever builds step addons |
| `data generator addon` | no generator produces this value | whoever builds generator addons |
| `unresolved element` | the element could not be resolved from source or tenant | the Operator, by capture |
| `no catalogue` | this build has no Catalogue for the application's platform | whoever ships catalogues |
| `declined` | expressible, and not converted on purpose | nobody — this is the refusal |

The first two are the ones that get merged by accident, and they are the two that
must not be. Both present as a step that cannot be finished; they are different
requests to different people. Where a step is missing *and* a value inside it has
no generator, the Cause is `step addon` — the generator question does not arise
until something can hold it.

Everything a fixed Cause cannot carry goes in `Reasoning`, which stays prose and
is what lets a ruling be overturned.

**`residue/<test>.md`** — one document per assembled test, naming what that test
could not do. Written at assembly, because a Residue row only becomes a specific
absence in a specific test at the moment that test is built.

It does not duplicate `residue.md`; the two are keyed differently on purpose and
answer different questions. `residue.md` is keyed by Source Step, so it answers
"what must be built to unblock the Migration" and one entry may cover forty
tests. The per-test document answers "what does *this* test not cover", which is
the question asked by whoever has to decide whether to trust a run of it. Neither
key can be derived from the other by sorting, because one row maps to many tests
and one test collects many rows.

Each entry names the marker block that stands in the test, so the document and
the test can be read against each other.

**`check-record.md`** — which checks ran against which Unit of Work. A check that
could not run is recorded as not checked, never as a pass. When the CLI gains a
check it did not have, the Units converted before it are marked as not checked
against that capability rather than inheriting a pass they never earned.

## Skeletons

Survey creates all seven. Six of them start empty, and they are created anyway so
that a later session finds the same shape every time and does not invent one. Write
these exactly; a Migration's files are read by several skills and by a person.

`residue/` is not among the seven and survey does not create it. Its documents
are per test and cannot exist before a test does, so assembly creates the
directory when it writes the first one. An absent `residue/` means no test has
been assembled yet, which is different from every assembled test being clean —
and a file that survey had pre-created empty could not tell those apart.

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
A Standing is `gap` or `refusal`.

| Source Step | Element | Cause | Standing | Reasoning | Revisit when |
|---|---|---|---|---|---|
```

`residue/<test>.md`:

```markdown
# Residue: <test name>

What this test does not do, and why. Each row stands in the test as a marker
block carrying the same label.

| Marker label | Source Step | Cause | Standing | What was needed |
|---|---|---|---|---|
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
