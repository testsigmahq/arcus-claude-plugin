# 01 — Test harness and manifest contract

**What to build:** A test suite that runs inside the testsigma plugin and fails when the
plugin's own paperwork is wrong. It checks that the plugin manifest and the marketplace
entry describing it are valid and agree with each other, and that the plugin's glossary
and ADRs are actually visible to version control. That last check exists because a broad
ignore rule silently hid every ADR in this plugin once already, and nothing noticed.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [x] The suite runs with one command and passes against the plugin as it stands today
- [x] It follows the existing arcus plugin's test style and dependency setup rather than introducing a new framework
- [x] The manifest is asserted to parse, and its name matches the marketplace entry that points at it
- [x] Every glossary and ADR file in the plugin is asserted to be tracked by version control, so a future ignore rule that hides them fails the suite
- [x] A helper exists for parsing a document's frontmatter, since every later ticket needs it
- [x] No test asserts exact wording, section order, or anything that makes rewording a document a failure

**Done, 2026-09-03.** 50 tests pass, 2 skipped (the skill and command
parametrisations, correct while neither exists yet). Committed in two commits: the
design record, and the suite.

Reviewed before commit, and the review found two genuine bugs in the helper that
thirteen later tickets build on. An indented `---` inside a YAML block scalar closed
the frontmatter and dropped every key below it into the body without raising, which
is exactly the shape a long skill description takes. And the ignore check could not
tell "not ignored" from "does not exist", so a deleted file read as visible. Both
fixed, both now have regression tests, and reverting either fix fails the suite.

Also from review: the semver pattern was unanchored and accepted trailing garbage; an
inline `mcpServers` object would have iterated its keys as if they were paths; one
collector guard compared a function to its own implementation and could not fail; the
module-level git skip could retire the ADR existence and numbering checks silently in
any non-git tree; and the ignore negation was wide enough to un-ignore generated build
output under any plugin. All corrected.

Twelve mutations verified in total, each caught and each returning to green when
reverted. The last two matter most because they came from the review rather than from
me: reverting the block-scalar fence fix, and reverting the missing-path guard.

Two deliberate deviations from the arcus prior art, both accepted at review. The
helper uses pyyaml rather than a hand-rolled parser, and the review's headline
finding was precisely the class of bug hand-rolling produces. And the visibility check
asserts that git does not ignore a file rather than that it is committed, with a
separate self-arming check for repository presence, so a file committed and later
deleted fails exactly one of the two.

**Found while doing this, not fixed here.** Before these commits the whole plugin was
untracked, so a remote install of it would have failed on a missing source while arcus
installed fine; local path installs worked, which is why nobody noticed. The commits
close that. Two pre-existing issues are left alone as out of scope: the `renames` key
in the marketplace manifest is not part of that schema and does nothing, and
`privacyPolicy` may not be a recognised manifest field, which would mean the privacy
disclosure added earlier surfaces nowhere.
