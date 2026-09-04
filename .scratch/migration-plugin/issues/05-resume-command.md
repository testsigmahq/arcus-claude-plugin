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

- [x] One command reports the active Phase and the next thing to do, unambiguously
- [x] Unreviewed Step Map rows are reported as a count and are locatable
- [x] Unanswered questions are surfaced every time, so an ignored question cannot go quiet
- [x] A CLI build that differs from the one recorded at the start is reported as a change, before it can silently alter what a check means
- [x] Reports correctly against a Migration that has only just been surveyed and has no mapping yet
- [x] Tests assert the command names all four things it must report

**Done, 2026-09-04.** 176 tests pass. `/testsigma:resume` is a command rather than a
skill: it is invoked deliberately at the start of a session, not matched against a
request.

The Phase is read off the Migration Directory by a stated rule — a four-row table,
first match wins — rather than by impression, so two sessions reading one directory
name the same Phase. The just-surveyed case is called out explicitly, because a Step
Map holding only its header gives zero unreviewed rows, and zero must not read as
nothing left to do.

The CLI comparison runs before anything else is reported and is the command's one
write: Units of Work checked under the old build are marked as not checked against
any capability the new build has gained.

Reviewed, and the review earned its keep twice.

**Five surviving mutations, one root cause.** Every one hedged or inverted an
instruction while keeping the words the assertion looked for — "you may mention it
later if it seems relevant", "it is fine to reduce a question to a count", and worst,
"you may create the directory yourself and fill in a reasonable guess", which reverses
the command's read-only charter. Fixed by asserting positively where a positive
exists ("report it before anything else", "do not create") rather than reaching for
another `absent` guard, plus a new test pinning which row of the Phase table wins.
All five now fail.

**One unexecutable instruction.** The element-resolution row tested "no elements are
resolved yet", and nothing in the seven files records that. A real rule with no way
to evaluate it, in the one section that exists to remove ambiguity. `migration.md`
now gains an Element Resolution section when that Phase completes, and its absence is
the signal — so the row is checkable today and stays correct when ticket 11 adds a
no-locators adapter.

**Two fixes outside this ticket.** `has_paragraph_with` now normalises whitespace
before matching: a phrase straddling a markdown line wrap silently failed, twice, and
the fix looked like reflowing prose to please a test. And the Step Map status
vocabulary (`unreviewed`/`reviewed`/`residue`) went into the Migration Directory
reference rather than into this command, since ticket 7 writes those rows and resume
counts them — separate statements would drift, and a private fourth value would be
counted as neither.

**Noted, not fixed.** I set a polarity trap on myself: an `absent` guard naming an
inversion matched the document's own correctly-negated sentence. The `absent` list is
as polarity-blind as the positive terms.
