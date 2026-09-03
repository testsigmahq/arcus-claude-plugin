# 05 — Resume command

**What to build:** The multi-session backbone. One command, run in a fresh session, reads
the Migration Directory and says where the work stands: which Phase is active, which Step
Map rows are unreviewed, which questions are unanswered, and whether the installed CLI has
changed since last time.

A Migration runs over many days and every session starts blank. Today the only way to pick
up the work is to read a handoff document and reconstruct the state by hand. Starting a
session should be one command.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] One command reports the active Phase and the next thing to do, unambiguously
- [ ] Unreviewed Step Map rows are reported as a count and are locatable
- [ ] Unanswered questions are surfaced every time, so an ignored question cannot go quiet
- [ ] A CLI build that differs from the one recorded at the start is reported as a change, before it can silently alter what a check means
- [ ] Reports correctly against a Migration that has only just been surveyed and has no mapping yet
- [ ] Tests assert the command names all four things it must report
