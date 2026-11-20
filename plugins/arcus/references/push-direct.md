# Push in direct mode

Read by `/arcus:push` when `arcus project mode show` says `direct`. A test and an element both go to Arcus, at once. The
team sees them. Modes and results are in `${CLAUDE_PLUGIN_ROOT}/references/workflow.md` and
`${CLAUDE_PLUGIN_ROOT}/references/states.md`.

## Files

Paths: the files the user named, or the files you just changed, else no path (the whole project; files that did not
change come back `unchanged`). There is no case to bind. The first push makes the file an Arcus test.

## The dry run

The JSON has `destination` (`project` and `folder`, each an `id` and a `name`, the name `null` when Arcus would not give
it; `region`; `arcusUrl`) and `files[]`. Each file has `result`, `message`, `diagnostics` and for a test a `plan` (`keep`,
`edit`, `new`, `remove`, `move`). Read each file's `result`. Do not read `summary`: it counts only the offline findings.

## The plan, in words

Begin with the place: `This goes to the Arcus project "<project>", in the folder "<folder>", at <arcusUrl>.` A name that
is `null`: give the id and say Arcus did not give the name.

Then one line per file: `created` is a new Arcus test with N steps; `updated` changes N steps (steps changed in Arcus
are merged into the file: `fromArcus`); `renamed` changes the title for everyone; `conflict` and `refused` are not sent
(give the reason); `missing` is skipped. Call out: how many new tests, any rename, and a changed element with how many
tests use it (its whole locator list is replaced for all of them).

## Before the yes

If the file was never run here, say it once and offer a run (`/arcus:run`). Do not hold a direct push back for it. If the
last run failed, say so. A failure caused by the app is a finding, not a reason to change the test.

## After the push

Say: `Pushed to the Arcus project "<project>", folder "<folder>".` Never say only "pushed". Always give the `url` of each
pushed test as a link. A CLI with no `url` gives none: then say to open `arcusUrl`, the project, the folder, and look for
the title. Never build a link yourself. A new test is in the folder shown. An updated test stays where it was.

The CLI rewrites each pushed file to Arcus's text. Tell the user to read `git diff`. Server lines (`serverProblems`,
`serverWarning`) never undo a push: read them out and offer `/arcus:author`.

## Failures to explain

| You see | Tell the user |
|---|---|
| `check_failed`, `refused` with diagnostics | The offline check failed. `/arcus:author` fixes it |
| `refused: A test named "…" already exists` | Another test has that title. Pick another |
| `conflict` | The same step changed in Arcus and in the file. Undo the local edit to it, or make the file equal Arcus's text. Delete the base in `.arcus/base/` only if the user says to |
| Whole-run error, exit `3` | A QI flag in a direct project, or a lock that does not fit the mode (`/arcus:mode`). Give the message and its `remediation` |
