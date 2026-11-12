# Changelog

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
