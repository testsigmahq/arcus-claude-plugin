---
description: Resume a Migration in a fresh session — report the active Phase, unreviewed Step Map rows, unanswered questions, and whether the installed testsigma CLI has changed
---

# Resume a Migration

A Migration runs over many days, and every session starts blank. This is the
session entry point: it reads the Migration Directory and says where the work
stands, so picking the work up is one command rather than an act of archaeology.

Read only. Nothing here writes to the Migration Directory except the one case
Step 2 names, and that case is a correction to a record that has become wrong.

**Who you are talking to.** The person running a Migration is the Operator.
They know Testsigma and do not necessarily read code, so nothing you put in
front of them carries code, a file path, a stack trace or a diagnostic code.
Those go in the Migration Directory. [../references/asking.md](../references/asking.md) is the
rule for what a question may contain; this does not restate it. See
`CONTEXT.md` for the vocabulary this plugin uses with them.

The file set this reads is defined in
[references/migration-directory.md](../references/migration-directory.md). Read
it there rather than assuming a shape.

## Before anything: is there a Migration here?

Look for `.testsigma/migration/` at the suite root. If it is absent, there is
nothing to resume: tell the Operator this suite has not been surveyed yet and
that survey is what starts a Migration. Do not create the directory here and do
not guess at the state — survey pins a snapshot and probes the CLI, and a
directory conjured without those facts is worse than none.

If the directory exists but a file the reference names is missing, say which and
stop. A partial directory means a session was interrupted mid-write, and reading
around the gap would report a state that was never true.

## Step 1: Re-probe the CLI and compare it against the recorded build

Do this first, before reading any of the work, because a check whose meaning has
changed silently is worse than a check that is missing.

Follow `references/cli-probe.md`, which says which program to confirm you are
talking to and what counts as the build's identity. Compare what you find against
the build recorded in `migration.md`.

If the installed build differs from the recorded one, report that change before
anything else in this session. Say it in consequences rather than as two
identifiers: the tool that checks this work is not the tool that checked what is
already converted.

Then correct the record, which is the one write this command makes. Every Unit
of Work in `check-record.md` that was checked under the old build is marked as
not checked against any capability the new build has gained. It does not inherit
a pass it never earned. Amend `migration.md` with the new build and the date.

## Step 2: Name the active Phase

The Phase is read off the Migration Directory by a stated rule, not by
impression, so that two sessions reading the same directory name the same Phase.

Take the first row that matches, top to bottom:

| What you find | Active Phase |
|---|---|
| `migration.md` has no Enumeration numbers | extraction |
| The adapter declares `carries-locators: no`, and `migration.md` has no Element Resolution section | element resolution |
| `step-map.md` has rows still `unreviewed`, or has none at all | mapping |
| Every row is `reviewed` or `residue`, and Units of Work are still being built | assembly |

Element resolution is a Phase of its own only where the source carries no
locators. Where it carries them, resolution is part of mapping, and that row
never matches. Its absence is what makes the row true: survey does not write an
Element Resolution section, so it is missing until the stage that resolves
elements finishes and writes one. Do not test this by looking at the source —
the Phase is read off the record, not re-derived.

A Step Map holding no rows at all — only its header — is the commonest second
session: survey has run and mapping has not started. The active Phase is mapping
and the work ahead is the whole Step Map. Zero unreviewed rows must never be
reported as nothing left to do.

## Step 3: Count what is unreviewed

Count the rows in `step-map.md` by their status, and report the count of
`unreviewed` rows exactly. Never round it, never call it "some", and never leave
it out because it has not moved since last session.

Make the rows findable rather than merely counted, because a number the Operator
cannot act on is not a report. Say that they are the rows whose status column
reads `unreviewed`, and name the first few by their source text so they can find
where reviewing resumes. If the count is large, say how many rather than listing
them all.

Rows are not equal, so report the unreviewed ones that genuinely vary separately
from the rest. Those carry most of the judgement, and a plan built on an average
row front-loads the wrong work.

## Step 4: Surface every unanswered question

Read `open-questions.md` and `application-facts.md`. A question in either file
with no answer is unanswered, and every unanswered one is surfaced in full every
session, without exception and whether or not anything else has changed. This
file exists because the alternative was demonstrated: a question was asked once,
never answered, and nothing anywhere recorded that it was still open.

Never reduce a question to a count. "Three questions outstanding" is how a
question goes quiet; the text of each is what gets it answered. State each one,
say when it was raised and who it was put to, and say what is blocked while it
stands.

The rules that decide what an admissible question looks like, and which of the
two fact files a thing belongs in, are defined in
[references/asking.md](../references/asking.md).

`open-questions.md` holds questions put to the Operator. `application-facts.md`
holds things true of the application under test that only someone who knows it
can answer. Both are unanswered questions and both are surfaced; keep them apart
in the report, because who can answer one is the distinction that matters.

## Step 5: Report, and say what happens next

Tell the Operator, in their terms and in this order:

- whether the CLI build changed, and what that means for what has already been
  checked — first, or not at all if it did not change
- the active Phase, and what that Phase is for
- how many Step Map rows are unreviewed, and where reviewing picks up
- every unanswered question, in full, in both of its files

Then name the next thing to do, as one action rather than a list of options. A
report that ends in a menu has handed the archaeology back to the Operator, which
is the thing this command exists to stop.
