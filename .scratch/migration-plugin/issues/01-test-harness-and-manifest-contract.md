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

**Done, 2026-09-03.** 41 tests pass, 2 skipped (the skill and command
parametrisations, correct while neither exists yet). Every contract test was
mutation-verified: reinstating the broad `docs/` ignore rule, a manifest name that
no longer matches its directory, a marketplace source pointing at the wrong plugin,
a non-semver version, an ADR numbered with a gap, and a component directory nested
inside the manifest directory. All six were caught, and the suite returns to green
when each is reverted.

Two deliberate deviations, both flagged for review. The frontmatter helper uses
pyyaml rather than the arcus suite's hand-rolled parser, because skill frontmatter is
genuinely YAML and every later ticket builds on this parser. And the document
visibility check asserts that git does not *ignore* a file rather than that it is
*committed*, because commit state moves constantly during development while an ignore
rule hiding a file is a standing property, and hiding them is the fault that actually
occurred.
