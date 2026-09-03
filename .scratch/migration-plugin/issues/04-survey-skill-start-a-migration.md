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

- [ ] Starting a Migration is one action against a source folder, with nothing to prepare by hand first
- [ ] A source folder with no version control is refused, with a reason the Operator can act on
- [ ] The chosen adapter is named along with why it was chosen, before any other work happens
- [ ] The source is snapshotted, and the snapshot reference is recorded
- [ ] The installed CLI is probed for which checks it supports, and the build is recorded
- [ ] The Migration Directory is created inside the source suite, one file per concern, each readable and diffable on its own
- [ ] The Collapse Ratio is reported, with a warning when it is near 1.0 that there may be no vocabulary worth mapping
- [ ] Tests assert the skill's body requires the version-control refusal and the CLI probe
