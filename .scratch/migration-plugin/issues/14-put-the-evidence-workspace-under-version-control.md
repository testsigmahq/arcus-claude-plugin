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
