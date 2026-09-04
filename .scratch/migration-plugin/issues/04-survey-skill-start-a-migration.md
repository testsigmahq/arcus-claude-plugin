# 04 — Survey skill: start a Migration

**What to build:** An Operator points at a source suite and gets a Migration. The skill
picks a Source Adapter and says which and why, so a wrong reading can be corrected before
any work depends on it. It snapshots the source, asks the installed CLI what it checks and
records which build that was, creates the Migration Directory, and reports the Collapse
Ratio before mapping begins.

It refuses to start against a source folder with no version control. The Migration
Directory lives inside the source suite so the source repository versions it, which only
works if there is a repository. The first conversion's workspace was an unversioned temp
directory holding the only copy of everything, and this refusal is the direct response.

**Blocked by:** 02

**Status:** ready-for-agent

- [x] Starting a Migration is one action against a source folder, with nothing to prepare by hand first
- [x] A source folder with no version control is refused, with a reason the Operator can act on
- [x] The chosen adapter is named along with why it was chosen, before any other work happens
- [x] The source is snapshotted, and the snapshot reference is recorded
- [x] The installed CLI is probed for which checks it supports, and the build is recorded
- [x] The Migration Directory is created inside the source suite, one file per concern, each readable and diffable on its own
- [x] The Collapse Ratio is reported, with a warning when it is near 1.0 that there may be no vocabulary worth mapping
- [x] Tests assert the skill's body requires the version-control refusal and the CLI probe

**Done, 2026-09-04.** 152 tests pass, 1 skipped. Adds the `survey` skill and two
shared references, `migration-directory.md` (the seven files and a skeleton for each)
and `cli-probe.md` (the procedure ADR-0003 only stated as policy).

**The CLI probe turned out to be the substantial part.** Two different programs are
called `testsigma`, and on this machine the one first on PATH is the wrong one: it
authors individual tests and has none of the workspace commands a Migration needs. A
skill that merely ran `--version` and proceeded would have used it silently. The
workspace CLI also has no `--version` at all and reports package version `0.0.0`, so
the build identity is the resolved path plus the commit of the checkout. Its help
surface is the only capability signal available, and specific flags are evidence of
specific checks. All of that is now written down rather than assumed.

**Two reviews, and both found real defects.**

The skill review found that three of six steps were unexecutable: the source folder
was never established, the adapter path was ambiguous relative to the skill, and Step
3 stated a policy with no procedure. It also found an ordering fault worth more than
the rest: the Collapse Ratio question was put to the Operator before
`open-questions.md` existed, so an unanswered question had nowhere to go, which is
precisely the failure that file was created to prevent. Directory creation and its
commit now happen before enumeration, so the expensive step is the only recoverable
loss. And the highest-value addition it suggested: check `git check-ignore` before
writing, because a repository that ignores dot directories makes every commit of the
Migration's state silently do nothing.

The code review broke the tests four ways, all now closed. The worst was a duplicate
heading: `markdown_sections` kept the last section of a given name, so gutting the
real refusals section and appending a verbatim copy after the last step passed every
gate. That is a worse false green than the whole-document vocabulary bug that section
scoping was introduced to fix. It also showed that co-occurrence cannot read polarity,
since "do not refuse" contains "refuse", and inverted two gates while keeping the
suite green.

**On polarity, honestly.** Named inversions are now forbidden per gate, which closes
the cheap ones. No string test closes the general case. That limit is written into the
helper rather than papered over.

Six bypasses re-run and all six now fail the suite: the duplicate-heading decoy, both
inverted gates, the pointer moved out of the step that creates the directory, an
eighth file added to the reference but not declared, and a renamed heading.

**One workflow fix.** Stale bytecode produced a second false failure. Test support
modules no longer write `.pyc` at all, because a mutation battery that can lie to you
is the thing you trust when you stop looking.
