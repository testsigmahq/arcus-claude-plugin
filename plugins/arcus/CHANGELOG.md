# Changelog

## 0.11.1

The skills match the final JSON output and exit codes of the renamed CLI. Only text changed.

- `references/commands.md` has a new part, "The output contract". With `--json`, every result has `ok`. A failure is one
  object on stderr with `ok: false`, `code`, `exitCode`, `message` and `remediation`. A wrong command line exits `3`
  with the code `USAGE`. `arcus help --json` is the source of truth.
- `arcus project list --json` is an object, `{ok, projects: [...]}`, not a plain array. The `setup` skill says so.
- `references/states.md` and `references/running.md` name the failure fields and codes, and the `ok` field of a run.
- `arcus --version --json` prints `{"ok":true,"version":"..."}`. The `setup` skill says so.

## 0.11.0

The skills use the new command names. Every command is now `arcus <entity> <command> [args]`. The old names are gone and
have no aliases. This version needs a CLI that has the new names.

- `arcus init` is `arcus project init`.
- `check`, `fmt`, `run`, `push`, `pull`, `status`, `accept`, `attach` and `detach` are now under `arcus test`, for
  example `arcus test push --dry-run`.
- `arcus context --issue <KEY>` is `arcus issue show <KEY>`. `arcus context --case <id>` is `arcus case show <id>`.
  `arcus verify --issue <KEY>` is `arcus issue verify <KEY>`. The other flags did not change.
- `arcus docs` is `arcus docs list`. `arcus docs <action>` is `arcus docs show <action>`, and the guides are
  `arcus docs show --topic <id>`.
- `arcus browsers list` is `arcus browser list`. `arcus devices list` is `arcus device list`.
- `arcus project platforms`, `arcus project sources` and `arcus project mode` now say `list`, `list` and `show`.
- `references/commands.md` says that `arcus help --json` prints the full command tree and is the source of truth.
- The skill names did not change. The document tests and the eval cases use the new names.

## 0.10.0

The Android guidance now matches the current CLI and real runs on an Android emulator.

- `setup`: the tools folder and the order the CLI reads it in (shell variable, `.env`, `arcus config set`, then the usual
  SDK places), the rule that a `.env` value must be an absolute path outside the repository, and that the CLI starts and
  stops Appium itself. The agent never writes a `.env` file without a yes.
- `run` and `verify`: `--platform` rules, `--device`, `--app` (and what `android.app` in `arcus.json` may hold), the
  `android` block, the `device:` and `tools:` lines, and the exit codes. A failed Android step often says only
  `Step failed`: read `results.ndjson` and the screenshot first.
- `references/running.md`: new parts "Android: tools, device, app" and "Android troubleshooting" (symptom, cause, next
  step), more setup errors, and the run evidence per test path and platform. A push with an `optional` run policy and no
  run shows `no local run`.
- `references/platforms.md`: "Writing for Android": what works, the locators that work, what `arcus check` refuses, the
  web-view-only locators, and the forms to avoid. What is not tested on a device yet is said as it is.
- `author`, `elements.md`, `reading-the-app.md`, `commands.md`, `push`, `help` and the README follow.

## 0.9.0

A near full rewrite for the QI workflow. Written against the `arcus` CLI that has `context`, `pull`, `accept`, `status`,
`attach`, `detach` and `verify`.

- New: the two project modes (`direct` and `qi`) in every skill, and a `mode` skill that shows and switches them.
- New skills: `context`, `verify`, `accept`, `sync` (status, pull, detach, attach, the pipeline check) and `mode`.
- `push` works in both modes: it covers the case flags, the run a QI push can require, and every refusal reason.
- `run` covers Android (`--platform`, `--device`, `--app`), the run note, and the run as evidence for a push.
- `setup` checks the mode, the Android tools and devices, and the QI commands.
- New references: `workflow.md`, `commands.md` (all QI command strings in one table) and `states.md` (states, refusal
  reasons, exit codes).
- The old design notes are removed.
- The Android part was written from the CLI's working copy. It was not yet committed in the CLI. Check it against the
  released CLI.

## 0.8.0

Added the `run` skill. Earlier versions: `setup`, `author` and `push` for direct mode.
