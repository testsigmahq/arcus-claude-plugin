---
description: Resume a Migration in a fresh session — report the Conversion queue and which Conversion is next, unreviewed Step Map rows, unanswered questions, and whether the installed testsigma CLI has changed
---

# Resume a Migration

A Migration runs over many days, and every session starts blank. This is the
session entry point: it reads the Migration Directory and says where the work
stands, so picking the work up is one command rather than an act of archaeology.

Read only. Nothing here writes to the Migration Directory except the one case
Step 1 names, and that case is a correction to a record that has become wrong.

**Who you are talking to.** The person running a Migration is the Operator.
They know Testsigma and do not necessarily read code, so nothing you put in
front of them carries code, a file path, a stack trace or a diagnostic code.
Those go in the Migration Directory. They are copied here rather than pointed
at because a question arises mid-work; `${CLAUDE_PLUGIN_ROOT}/references/asking.md`
decides them and covers everything else shown to the Operator. See
`${CLAUDE_PLUGIN_ROOT}/CONTEXT.md` for the vocabulary this plugin uses with them.

The file set this reads is defined in
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`. Read
it there rather than assuming a shape.

## Before anything: is there a Migration here?

Look for `.testsigma/migration/` at the suite root. If it is absent, there is
nothing to resume: tell the Operator this suite has not been surveyed yet and
that survey is what starts a Migration. Do not create the directory here and do
not guess at the state — survey pins a snapshot and probes the CLI, and a
directory conjured without those facts is worse than none.

If the directory exists but a file the reference names is missing, stop, and say
which record is absent in the terms the Operator knows it by — the Step Map, the
check record, the open questions — rather than which file. A partial directory
means a session was interrupted mid-write, and reading around the gap would
report a state that was never true.

## Step 1: Re-probe the CLI and compare it against the recorded build

Do this first, before reading any of the work, because a check whose meaning has
changed silently is worse than a check that is missing.

Follow `${CLAUDE_PLUGIN_ROOT}/references/cli-probe.md`, which says which program to
confirm you are talking to and what counts as the build's identity. Compare what you
find against the build recorded in `migration.md`.

If the installed build differs from the recorded one, report that change before
anything else in this session. Say it in consequences rather than as two
identifiers: the tool that checks this work is not the tool that checked what is
already converted.

Then correct the record, which is the one write this command makes. Every Unit
of Work in `check-record.md` that was checked under the old build is marked as
not checked against any capability the new build has gained. It does not inherit
a pass it never earned. Amend `migration.md` with the new build and the date.

`${CLAUDE_PLUGIN_ROOT}/references/checks.md` defines the six checks and
this rule. Report the count of Units now not checked against the new capability,
so re-checking is the Operator's costed decision rather than an oversight.

## Step 2: Read the Conversion queue off `scenarios.md`

A Migration delivers one Conversion at a time, so what a fresh session needs is
the queue: what is done, what is pending, what is parked and what each parked
scenario waits on, and which Conversion would be taken next.

Read `scenarios.md` and count its rows by status — `done`, `pending`, `parked`
and `out-of-scope`. Report all four counts every session, including the ones that
are zero, because a status left out reads as a status nothing is in. Lead with
**tests delivered of total scenarios**: that is the number a customer onboarding
onto Testsigma counts progress in. A Migration that has been surveyed and not
yet converted leads with none delivered of its total, and that is a queue waiting
to be worked rather than a Migration with nothing in it.

**Name every parked scenario and what it waits on**, taking the `Reason` from its
row. Never reduce them to a count. A parked scenario is the one part of this
report the Operator alone can clear, and "two parked" is how a question goes
quiet. Where what a row waits on has since cleared, say so and say that the next
Conversion returns it to `pending` — that is `convert`'s write, not this one's.

Name `out-of-scope` rows with their reasons on request rather than in full every
session. They were ruled out by someone who looked, and re-reading the ruling
every session is what makes a report skimmed.

**Name the Conversion that would be taken next.** Run
`${CLAUDE_PLUGIN_ROOT}/scripts/next_conversion.py --suite <the suite>`, which is
the same script `convert` runs and reads without writing. Using the script rather
than an impression is what stops resume and convert naming different scenarios,
which would make the queue unreadable in exactly the way one session's judgement
call always does. Do not convert it here: this command reports, and `convert`
takes it.

Where the script reports that vocabulary has saturated, the scenario it names is
a default rather than a recommendation. Say so, and ask the Operator which
scenarios the customer wants first: from that point ordering has handed over to
their priority, and a default presented as a recommendation takes that choice
away from them without their knowing it was theirs.

If the script selects nothing, say which of the two it is — every scenario
delivered, or every remaining one parked or out of scope — rather than reporting
silence. They are different states and only one of them is a finished Migration.
A script that cannot find the records it reads is neither: that is the partial
directory the opening section stops on, and it is reported as a missing record
rather than as a Migration with nothing left to convert.

Nothing here is relayed to the Operator as the script prints it. Its output names
files and paths, which is the detail the audience rule above keeps out of what
they see; the counts and the scenario name are what is theirs.

## Step 3: Count what is unreviewed

Count the rows in `step-map.md` by their status, and report the count of
`unreviewed` rows exactly. Never round it, never call it "some", and never leave
it out because it has not moved since last session.

A Step Map holding no rows at all — only its header — is the commonest second
session: survey has run and no Conversion has been taken. Zero unreviewed rows
must never be reported as nothing left to do; the rows arrive as Conversions
reach them, so the work ahead is the whole queue rather than the rows on file.

Make the rows findable rather than merely counted, because a number the Operator
cannot act on is not a report. Say that they are the rows whose status column
reads `unreviewed`, and name the first few by their source text so they can find
where reviewing resumes. If the count is large, say how many rather than listing
them all.

**Count the Concessions too, and list them.** A row marked `Concession:` in
`step-map.md` is reviewed work carrying a known, accepted difference from the
source. Report the count every session and name them on request, because a
Concession that nobody can find again is a Divergence — the whole difference
between the two is whether the difference stays visible. Read
`platform-facts.md` alongside them for the limits that forced them, since a limit
that has since been lifted turns a Concession back into a row worth redoing.

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
`${CLAUDE_PLUGIN_ROOT}/references/asking.md`.

`open-questions.md` holds questions put to the Operator. `application-facts.md`
holds things true of the application under test that only someone who knows it
can answer. Both are unanswered questions and both are surfaced; keep them apart
in the report, because who can answer one is the distinction that matters.

## Step 5: Report, and say what happens next

Tell the Operator, in their terms and in this order:

- whether the CLI build changed, and what that means for what has already been
  checked — first, or not at all if it did not change
- the Conversion queue — delivered of total, pending, parked with what each
  waits on — and the Conversion that would be taken next
- how many Step Map rows are unreviewed, and where reviewing picks up
- every unanswered question, in full, in both of its files

Then name the next thing to do, as one action rather than a list of options. A
report that ends in a menu has handed the archaeology back to the Operator, which
is the thing this command exists to stop.

**Where the queue is empty, say that the work is not delivered.** Every
Conversion ends at a committed working copy and none of them pushes, so a
Migration with nothing pending has produced every test and sent none of them.
Nothing else in a session says this: the stages report what they finished, and a
reader who has watched each one succeed reasonably concludes the work arrived.

Say it and stop there. Delivery is **the Operator's** act at a moment they pick,
and this command neither performs it nor offers to —
`${CLAUDE_PLUGIN_ROOT}/references/delivery.md` holds what it involves, including
the one write that reaches past the version being delivered into.
