# 26 — Uploads are pushable, and one kind of push escapes the target

**What to build:** The plugin treats uploads as pull-only. `adoption.md` runs
`pull uploads --write` and nothing anywhere sends one. Uploads are pushable, and the
way they push breaks a rule the rest of the plugin can keep.

**The mechanic.** An `upload` line without `[id = N]` is always a POST — a new upload,
every time. No filename matching, no name matching, no heuristic. If the application
already holds an upload of that name you get a second one beside it. With `[id = N]` it
is a PUT, and each id-less `version` block under it mints a new version. The bytes come
from `localFilePath`, which is removed in the same write that binds the minted id, so a
pushed file is the canonical pulled form: safe to commit, and a re-push is a no-op
(`TSS1110`) because nothing is left to send.

**Why this one escapes.** Uploads are application-scoped. The working copy lives under
the application directory, not the version's, and no route takes a version. Worse, when
a new version lands the server repoints **every referencing step** at it — including
steps in other versions of the same application. A step somewhere else that pinned that
upload now resolves to bytes this Migration sent.

So per ADR-0014: creating a **new** upload is free, because nothing references it yet.
Adding a version to an **existing** upload happens only where the Operator says so for
that upload, with the versions that would be repointed named first. Consent is per
upload, and "the Operator agreed to a push" is not it.

**The blast radius cannot be enumerated, and must be reported that way.** There is no
route from an upload to the steps that reference it — not in the command-line tool, not
in the server. The one usages mechanism covers step groups, test data profiles and
elements; uploads are absent from it, so an upload push has never reported a usage and
`TSS1110` "used by N other tests" does not arrive for one.

What *can* be listed is worse than nothing: the workspace holds the tests of the version
the Operator is attached to, and those are exactly the steps that are **not** at risk.
The repointing does its damage in the application's *other* versions, which is the part
no query reaches. So a list assembled from the workspace would read as a survey of the
blast radius while containing none of it.

Name none rather than the safe ones. The plugin asks for consent saying plainly that it
cannot tell which steps elsewhere would be repointed, and the Operator decides knowing
that. A blast radius reported as empty because nobody could look is the failure this
whole plugin exists to prevent, arriving at the scale of another team's test run.

**Refusals worth knowing:** `TSS1157` bound and carrying a path (a version's bytes cannot
be replaced; move the path to a new id-less block). `TSS1156` id-less with no path.
`TSS1117` two id-less blocks of one name. `TSS1201` baseline mismatch, with no
`--overwrite-remote` offered, because every upload write appends. Uploads are excluded
from `--delete`.

**Blocked by:** 29.

**Status:** ready-for-agent

- [ ] The upload push is described where the push story lives, not in adoption
- [ ] A new upload and a new version of an existing one are separated, with the reason
- [ ] The rule states that a version push escapes the target version, and what it reaches
- [ ] Consent is per upload, and the affected versions are named before it is asked for
- [ ] The plugin states that the affected steps cannot be enumerated, and asks anyway
- [ ] It does not list the workspace's own steps as though they were the blast radius
- [ ] `TSS1110` is not implied to arrive for an upload
- [ ] `pull uploads --write` against the target is named as how to avoid authoring a twin
- [ ] The refusal codes are named with what each means for a Migration
- [ ] No document still implies uploads are pull-only
