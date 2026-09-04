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

**Who you are talking to.** The person running a Migration is the Operator. They
know Testsigma and do not necessarily read code, so nothing you put in front of
them contains a command, a file path, a stack trace or a diagnostic code. Those go
in the Migration Directory. See `CONTEXT.md` for the vocabulary this plugin uses
with them.

## Step 0: Establish which folder is the source suite

Before any check, decide what "the suite" means here, because everything else is
relative to it. It is the directory that contains the tests being migrated, which
is often not the root of the repository holding them.

Ask the Operator if there is any ambiguity. A monorepo, or a suite sitting in a
subdirectory beside application code, is the normal case rather than the exception.

The Migration Directory goes at the suite root you settle on, even when the
repository root is higher up. Say which folder you chose.

## Before anything else: three refusals

Check all three before doing any work, cheapest first. Each is a stop, not a
warning.

**A Migration must not already exist.** If `.testsigma/migration/` is present in
the suite, this suite has already been started. Do not start again and do not
overwrite it. Say what is already recorded there and resume instead.

**The CLI must be installed, and be the right one.** Run `testsigma --version` and
read its help. Two different programs are called `testsigma` and only one can run a
Migration; `references/cli-probe.md` says how to tell them apart. If it is absent
or it is the wrong one, stop. Tell the Operator that the Testsigma command-line
tool this needs is not available on this machine, so nothing produced here could be
checked, and ask them to install it or say who can.

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
silently useless rather than absent:

**The suite must not ignore the Migration Directory.** Check with
`git check-ignore -q .testsigma/migration`. Plenty of repositories ignore dot
directories wholesale. If this one does, every commit of the Migration's state
silently does nothing, which is the exact failure version control was required to
prevent, arriving quietly. Stop, and tell the Operator the suite is configured to
discard this folder.

**Notice a submodule.** If the suite is its own repository nested inside another,
its state commits somewhere the Operator may not expect. Do not refuse; say which
repository will hold the Migration's notes and confirm that is what they want.

## Step 1: Choose the Source Adapter, and say why

Read the adapters in `${CLAUDE_PLUGIN_ROOT}/adapters/`, starting with `README.md`
there, which defines the format and what the three properties mean.

Name the adapter you chose and say why you chose it, before any other work
happens, so a wrong reading can be corrected before anything depends on it. The
reason matters as much as the choice: an Operator cannot correct a decision whose
grounds they cannot see.

Report its three declared properties in plain consequences rather than as field
values: whether the real sequence hides behind a helper layer, which decides how
costly checking each step against the source will be; whether the source carries
locators, which decides whether finding elements is part of mapping or a stage of
its own; and whether values carry a language of their own.

If two adapters plausibly match, do not pick quietly. Say which two and what
distinguishes them, and let the Operator settle it. If none matches, stop, say
which formats are supported, and offer to write an adapter for this one.

## Step 2: Pin the source snapshot

Record the commit the suite is at, and the branch it is on. If the checkout is on a
detached HEAD, record that instead of a branch, because a commit with no branch is
much harder to find again later.

That commit is the snapshot. Because the suite is under version control, the
snapshot is a reference rather than a copy, which is the whole reason the previous
step refuses a folder without it.

If the working tree has uncommitted changes, tell the Operator how many files
differ and offer to save them first. Do not list paths at them. A Migration pinned
to a commit while the tree differs from it is a fact they need, not a detail to
smooth over.

## Step 3: Probe the CLI and record what it checks

Follow `references/cli-probe.md`. It says which program to confirm you are talking
to, what to record as the build, and how to read the help surface as evidence of
which checks this build performs.

Never assume a check exists. A later stage relying on a diagnostic the installed
build does not produce must record that check as not covered rather than as
passing, and it can only do that if this step wrote down what was actually
available. Diagnostic codes belong in the Migration Directory and are never spoken
to the Operator.

## Step 4: Create the Migration Directory and commit it

Do this before enumerating, not after. Enumeration is the long step, and everything
established so far is a cheap fact that would be lost with the session. Committing
now also means the next step has somewhere to put a question.

Create `.testsigma/migration/` at the suite root and write its files, one per
concern. The file set, what each holds, and a skeleton for each are defined in
[references/migration-directory.md](../../references/migration-directory.md). Do
not restate the list here or invent a file that is not in it.

Write `migration.md` with what Steps 0 to 3 established. Create the other six from
their skeletons. Then commit just this directory, with `git add .testsigma/migration`
and a message of the form `chore(migration): start migrating <suite>` — never a
bare commit of everything, which in a monorepo sweeps up unrelated work.

State is only kept if it is committed, which is the whole point of putting it here.

## Step 5: Enumerate the Source Steps

Follow the chosen adapter's own Enumeration section. It states the rule that
decides when two source lines are the same Source Step, and that rule belongs to
the format, not to this skill.

The counting is mechanical and the suite may hold thousands of lines, so write a
throwaway script from the adapter's numbered rule rather than counting by reading.
This is the one part of reading a source that may be automated: the rule is exact
by construction. Everything else the adapter asks for is judgement and is never
scripted.

Report:

- total source steps written, and distinct Source Steps
- the **Collapse Ratio**, total divided by distinct
- how many Source Steps occur exactly once
- the parameterisation profile: how many carry no parameter, how many carry one the
  suite only ever fills a single way, and how many genuinely vary

**Warn when the Collapse Ratio is near 1.0.** Treat below 1.5 as the warning
threshold, as a guideline rather than a rule; a real suite measured for this plugin
sat at 7.86, and the adapter's own worked example at 1.88. A ratio near 1.0 means
every step is written once and there is no vocabulary to map, so mapping saves
nothing and the Migration will cost about what rewriting the suite by hand would.
That is a decision for the Operator, not a number to file. Put it to them, record
the question in `open-questions.md` immediately, and clear it only when they answer.

Two other numbers change how the work should be ordered, so report them as findings
rather than statistics. Source Steps occurring once amortise nothing, so a long tail
sets the floor cost. And rows are not equal: the ones that genuinely vary carry most
of the judgement, so a plan built on an average row will front-load the wrong work.

Amend `migration.md` with the enumeration and commit again.

## Step 6: Report, and hand over

Tell the Operator, in their terms:

- which adapter was chosen and why
- what the suite contains, and the Collapse Ratio with its warning if one applies
- what was recorded, and that it now travels with the suite itself so the next
  session finds it
- what happens next, which is mapping, and roughly how large it is in rows rather
  than in hours

Anything you could not settle goes into the Migration Directory before you finish:
a question for the Operator into `open-questions.md`, something learned about
Testsigma into `platform-facts.md`, something only they can answer about their own
application into `application-facts.md`. A question that exists only in this
session's transcript is a question that will be lost.
