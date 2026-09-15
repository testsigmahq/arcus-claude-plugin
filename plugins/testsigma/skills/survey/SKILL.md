---
name: survey
description: Use when someone wants to start migrating an existing automation suite into Testsigma — a Cucumber, Gherkin, Selenium, TestNG or Tosca suite — or asks to survey or size such a suite before converting it, as in "how big a job is this". Not for authoring a single new test. Picks the Source Adapter for the suite's format, pins a source snapshot, probes the installed testsigma CLI, enumerates the suite's distinct Source Steps and reports its Collapse Ratio, then creates the Migration Directory the later stages read.
---

# Survey: start a Migration

A Migration converts one source suite into Testsigma over many days and many
sessions. This is the stage that makes the rest possible: it decides how the
source will be read, pins what is being converted, measures whether the job is
worth doing, and creates the Migration Directory that every later session picks
up from.

Do this once per suite. It is the only stage that runs before there is anything
to resume.

**Who you are talking to.** The person running a Migration is the Operator.
They know Testsigma and do not necessarily read code, so nothing you put in
front of them carries code, a file path, a stack trace or a diagnostic code.
Those go in the Migration Directory. They are copied here rather than pointed
at because a question arises mid-work; `${CLAUDE_PLUGIN_ROOT}/references/asking.md`
decides them and covers everything else shown to the Operator. See
`${CLAUDE_PLUGIN_ROOT}/CONTEXT.md` for the vocabulary this plugin uses with them.

## Step 0: Establish which folder is the source suite

Before any check, decide what "the suite" means here, because everything else is
relative to it. It is the directory that contains the tests being migrated, which
is often not the root of the repository holding them.

Ask the Operator if there is any ambiguity. A monorepo, or a suite in a
subdirectory beside application code, is the normal case rather than the exception.

The Migration Directory goes at the suite root you settle on, even when the
repository root is higher up. Say which folder you chose.

## Before anything else: four refusals

Check all four before doing any work, cheapest first. Each is a stop, not a
warning. The first three, and the two confirmations that follow them, each cost a
command; the fourth costs the Operator a question, so it comes after everything a
command can settle.

**A Migration must not already exist.** If `.testsigma/migration/` is present in
the suite, this suite has already been started. Do not start again and do not
overwrite it. Say what is already recorded there and resume instead.

**The CLI must be installed, and be the right one.** Run `testsigma --version` and
read its help. Two different programs are called `testsigma` and only one can run a
Migration; `${CLAUDE_PLUGIN_ROOT}/references/cli-probe.md` says how to tell them
apart. If it is absent or it is the wrong one, stop. Tell the Operator that the
Testsigma command-line tool this needs is not available on this machine, so nothing
produced here could be checked, and ask them to install it or say who can.

**The source suite must be under version control.** Confirm it sits in a work tree
and that the branch has at least one commit, with `git rev-parse --is-inside-work-tree`
and `git rev-parse HEAD`. If either fails, refuse, and give the Operator the reason
rather than the command: the Migration keeps its notes inside this folder, so the
suite's own version control is what preserves them, and the snapshot it pins to is
a commit rather than a copy. Without version control there is nothing to pin to and
nothing to keep the state in. This refusal exists because it has already gone
wrong: the conversion that produced this plugin's design sat unversioned in a
temporary directory, holding the only copy of every artifact it had produced.

Two further checks belong with these, because both make the Migration Directory
silently useless rather than absent. Run both now, reading what each means in
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`:
`git check-ignore -q .testsigma/migration`, which stops the Migration if the suite
discards the folder, and whether the suite is a submodule, which does not stop it
but must be confirmed.

The fourth refusal comes after all of those because it is the only one that spends
the Operator's attention rather than a command's.

**The suite's platform must be one this build has a catalogue for.** Ask the
Operator which application in their Testsigma project this Migration targets, and
what kind of application it is. This build writes working copies for web and
unified applications only; an application on any other platform is refused the
first time a working copy is attached, before a single row has been converted.
The refusal is not a Web catalogue with holes in it — `cli-probe.md` says why, and
the consequence is that a suite driving another platform has no catalogue here at
all. If that is what this suite drives, stop. Tell the Operator which platforms
can be converted today and that theirs is not yet among them, so nothing produced
here could be attached.

Take the answer from the Operator, not from the source: a suite's own code is weak
evidence of the platform it drives, and the target application sits in their tenant.

Which platforms have a catalogue is a property of the installed build and it grows,
so this stop turns on what `cli-probe.md` found rather than on the pair named above.
Record the answer in `platform-facts.md` with how it was established.

## Step 1: Choose the Source Adapter, and say why

Read the adapters in `${CLAUDE_PLUGIN_ROOT}/adapters/`, starting with `README.md`
there, which defines the format and what the three properties mean.

Name the adapter you chose and say why, before any other work happens, so a wrong
reading can be corrected before anything depends on it. The reason matters as much
as the choice: an Operator cannot correct a decision whose grounds they cannot see.

Report its three declared properties in plain consequences rather than as field
values: whether the real sequence hides behind a helper layer, which decides how
costly checking each step against the source will be; whether the source carries
locators, which decides how much of finding elements the source can answer; and
whether values carry a language of their own.

If two adapters plausibly match, do not pick quietly. Say which two and what
distinguishes them, and let the Operator settle it. If none matches, stop, say
which formats are supported, and offer to write an adapter for this one.

## Step 2: Pin the source snapshot

Record the commit the suite is at and the branch it is on. On a detached HEAD,
record that instead of a branch: a commit with no branch is much harder to find
again later.

That commit is the snapshot: a reference rather than a copy, which is the whole
reason the previous step refuses a folder without version control.

If the working tree has uncommitted changes, tell the Operator how many files differ
and offer to save them first, without listing paths at them. A Migration pinned to a
commit while the tree differs from it is a fact they need.

## Step 3: Probe the CLI and record what it checks

Follow `${CLAUDE_PLUGIN_ROOT}/references/cli-probe.md`. It says which program to
confirm you are talking to, what to record as the build, and how to read the help
surface as evidence of which checks this build performs.

Never assume a check exists. A later stage relying on a diagnostic the installed
build does not produce must record that check as not covered rather than as passing,
which it can only do if this step wrote down what was available. Diagnostic codes
belong in the Migration Directory and are never spoken to the Operator.

## Step 4: Create the Migration Directory and commit it

Do this before enumerating, not after. Enumeration is the long step, everything
established so far would be lost with the session, and committing now means the next
step has somewhere to put a question.

Create `.testsigma/migration/` at the suite root and write its files, one per
concern. The file set, what each holds, and a skeleton for each are defined in
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`. Do
not restate the list here or invent a file that is not in it.

**Settle where the working copy will go, and write it down** on `migration.md`'s
`Working copy:` line — inside the suite, never beside it, per ADR-0011 and the
reference above. Left to assembly, each session picks again, and an unrecorded path
is one a resumed session cannot find.

Write `migration.md` with what Steps 0 to 3 established. Create the other eight from
their skeletons. Then commit just this directory, with `git add .testsigma/migration`
and a message of the form `chore(migration): start migrating <suite>` — never a
bare commit of everything, which in a monorepo sweeps up unrelated work.

State is only kept if it is committed, which is the whole point of putting it here.

## Step 5: Inventory what the target project already holds

Ask the Operator whether anyone has already converted part of this suite by hand.
A Migration that does not know what the project holds authors a second copy of it.

If they say yes, pull the project into `.testsigma/migration/existing/` and commit —
`testsigma pull version --write` and what hangs above the version, as
`${CLAUDE_PLUGIN_ROOT}/references/adoption.md` lists. That inventory lets mapping
adopt a step group rather than rebuild it, and element resolution reuse a team's
screen; the same reference says what must be true before a row may claim one.

**Ask whether the project may be written to.** A project holding work a team
depends on is often read-only, and only they hold that fact. Record it in
`application-facts.md`: every later stage decides where to push from it, and an
unrecorded read-only project is discovered by writing to it.

Record in `migration.md` what was pulled, or that the Operator said the project
was empty. An absent `existing/` must not read as "nobody looked".

## Step 6: Enumerate the Source Steps

Follow the chosen adapter's own Enumeration section. It states the rule that
decides when two source lines are the same Source Step, and that rule belongs to
the format, not to this skill.

The counting is mechanical and the suite may hold thousands of lines, so write a
throwaway script from the adapter's numbered rule rather than counting by reading.
This is the one part of reading a source that may be automated: the rule is exact by
construction. Everything else the adapter asks for is judgement and is never
scripted.

**Record which scenario each occurrence came from, in the same pass.** Keeping the
scenario a line sat in costs one extra column in a walk the script already makes,
and it must never become a second pass over the source. That scenario-to-Source-Step
incidence is what orders the Conversions later, and survey is the only stage that
walks the whole suite, so an incidence it discards is one nothing else can cheaply
rebuild.

Report:

- total source steps written, and distinct Source Steps
- the **Collapse Ratio**, total divided by distinct
- how many Source Steps occur exactly once
- the parameterisation profile: how many carry no parameter, how many carry one the
  suite only ever fills a single way, and how many genuinely vary

**Warn when the Collapse Ratio is near 1.0.** Treat below 1.5 as the warning
threshold, a guideline rather than a rule; a real suite measured for this plugin sat
at 7.86 and the adapter's worked example at 1.88. Near 1.0 every step is written
once, so there is no vocabulary to map and the Migration costs about what rewriting
the suite by hand would.
That is a decision for the Operator, not a number to file. Put it to them, record
the question in `open-questions.md` immediately, and clear it only when they answer.

**Screen for what is unconvertible before quoting a size**, and report those
scenarios as out of scope rather than counting them in the total. This screens step
content, and it is the second of the two triage axes: the platform gate above
settled whether the suite's application can be converted at all, and this settles
which of its scenarios can. What to screen for, what to anchor the classifier to,
and why a screened scenario is seeded rather than omitted are in
`${CLAUDE_PLUGIN_ROOT}/references/content-screen.md`.

Two other numbers change how the work should be ordered, so report them as findings
rather than statistics. Source Steps occurring once amortise nothing, so a long tail
sets the floor cost; and the rows that genuinely vary carry most of the judgement.

**Seed `step-map.md` with the distinct Source Steps, every row `unreviewed`.**
The enumeration just produced them, so this costs one write, and it changes what
mapping is: filling rows in rather than creating them.

The third of the three things that follow is why this is here rather than left to
mapping. Progress becomes a number from the first minute — *reviewed 12 of 55*; a
session that ends early resumes instead of re-reading; and a run reading source
without moving that count is visibly not progressing, where an empty map and an
unstarted one look identical. A measured run read step definitions for a hundred and
eighteen calls, wrote no row, and ended with nothing.

**Seed `scenarios.md` with one row per scenario, every row `pending`**, the
unconvertible ones `out-of-scope` with their reason, so what is left to convert and
what was ruled out are read together. The incidence just recorded holds the Source
Steps each one reaches, so this too costs one write. It is the Conversion queue, and
seeding it here is what lets a later session answer "what is next" without walking
the source again. Commit `scenarios.md` with the rest of the Migration Directory.

**The Step Map's seeding is unchanged by this.** Every distinct Source Step still
gets its own `unreviewed` row, in scope or not: the denominator and the anti-stall
signal both depend on the empty rows existing to be visibly unfilled.

Amend `migration.md` with the enumeration and commit again.

## Step 7: Report, and hand over

Tell the Operator, in their terms:

- which adapter was chosen and why
- what the suite contains, and the Collapse Ratio with its warning if one applies
- how many scenarios are in scope to convert, and how many were ruled out and why,
  since that is the count they will report to the customer
- what was recorded, and that it now travels with the suite itself so the next
  session finds it
- what happens next, which is the first **Conversion**: one scenario carried end
  to end, out of the scenario count above

Anything you could not settle goes into the Migration Directory before you finish:
a question for the Operator into `open-questions.md`, something learned about
Testsigma into `platform-facts.md`, something only they can answer about their own
application into `application-facts.md`. A question that exists only in this
session's transcript is a question that will be lost.

How a question is phrased, what it may never contain, and which of the two fact
files a thing belongs in are defined in
`${CLAUDE_PLUGIN_ROOT}/references/asking.md`. Follow it rather than
inventing a form here.
