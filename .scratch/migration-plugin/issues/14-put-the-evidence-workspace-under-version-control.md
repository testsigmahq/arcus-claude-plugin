# 14 — Put the evidence workspace under version control

**What to build:** Not plugin work. It is in this list so it does not get forgotten, which
is the exact failure mode the plugin's question tracking exists to prevent.

Every fact the plugin's design rests on came from one converted scenario, and that
conversion exists in a single unversioned copy in a temporary directory. There is no
repository and no history. The archive sitting beside it holds the original source only,
with no conversion inside it. The Testsigma tenant holds the pushed entities but not the
authored files, and pulling them back cannot reconstruct the folder layout or the
environment file.

So the evidence base for this entire spec is one accidental deletion away from gone. The
Migration that produced it would also fail the version-control refusal that ticket 04
introduces, which is worth stating plainly rather than quietly fixing.

Another session owns that path and was already raising this. Coordinate rather than writing
to it from here; two sessions writing one workspace is the concurrency problem the tooling
cannot see.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [x] The converted workspace is under version control, or copied somewhere durable and versioned
- [x] The converted test, step groups, screens, elements and both probe fixtures are all confirmed present in whatever now holds them
- [x] It is confirmed whether the original source archive should be kept as the snapshot, or replaced by a proper snapshot
- [x] Ownership of the path is agreed with the other session before anything writes to it
- [ ] A remote or off-machine backup exists, since the repository is local-only and a disk failure still loses everything
- [ ] The session transcript left out of history is either scrubbed and committed, or its substance extracted into a committed document

**Progress, 2026-09-03.** Committed in two commits: the pristine source as extracted,
which is now the snapshot as a real git object rather than an archive, and the
conversion separately. 578 files tracked, nothing uncommitted. Credential-bearing
files were excluded by name with stated reasons and left on disk: real-looking Maven
server credentials, and a session transcript carrying credential-shaped strings in
about thirty places. What remains is off-machine durability, which is the only part of
this ticket that still matters.

**Progress, 2026-09-04.** Two criteria remain open, deliberately rather than quietly.

**Off-machine backup: still open, and not mine to close.** The evidence workspace has
no remote, and giving it one means putting a third party's automation suite on a
hosted service. That is a decision about an agreement with them, not a technical
step, and no amount of asking from here changes that. Another session is also
actively committing to that path — three untracked paths appeared there during this
session — so nothing was written to it. Recorded as unmet.

**The transcript: dropped, and the record it left behind was wrong.**
`claude-convo.txt` is a pasted terminal scrollback from the original conversion
session — Claude Code v2.1.216, run from `~/Downloads/MAWM_SeleniumAutomation-TestSigma30`,
invoking `/arcus:test` to convert the Selenium scripts. Its substance is already
extracted into the glossary, the five ADRs, the collapse-ratio report and two
adapters whose numbers were verified against the real files, so nothing further is
needed from it. It stays gitignored where it is.

This ticket recorded "~30 credential-shaped strings" in it. That was overstated, and
the figure appears to have counted mentions rather than values. Measured: 130 lines
mention a credential-ish word — 49 of them "login", 38 "auth", ordinary prose about
signing in — and only **8 lines carry an actual value** after a delimiter. The
difference matters: it is not scattered contamination but eight known lines, which
would be tractable if anyone ever wanted the file. Nobody does.

**What this ticket did close, unexpectedly.** The plugin's own commits were pushed by
cherry-picking all fifteen onto a fresh branch off `prod`, excluding one arcus commit
that was not ours. On that clean branch two manifest tests failed at once: the
marketplace entry registering the `testsigma` plugin had **never been committed**. It
had lived the entire build as a working-tree edit, so those tests passed for thirteen
tickets on the strength of an uncommitted file, and a marketplace install would have
failed on a missing entry. Ticket 01's note that its commits had closed exactly this
problem was wrong — the dirty tree masked it, and only a clean checkout could show it.

Fixed and committed. `feat/testsigma-migration-plugin` is pushed with sixteen
commits, both suites green, and the plugin is now installable from the marketplace it
claims to be listed in.
