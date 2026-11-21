---
name: sync
description: Use when a developer asks where their Arcus test files stand, after QI changed a case (rework, rejection, a suggestion, a head that moved), on a fresh clone, or to keep a file as a local test. Checks the mode first. Runs arcus test status, arcus test pull, arcus test detach and arcus test attach, and explains every state in plain words with the next step. Also covers arcus test status --ci for pipelines. Pull is qi mode only. Not for pushing.
---

# Sync: where do my files stand?

This skill reads where each test file stands and brings the file and its case back in step. The states differ by mode, so check the mode first. Always give the `next` line the CLI prints.

## 1. Check the mode, then read one file

Run `arcus project mode show`. With several projects ask which one and pass `--project <folder name>` everywhere. Then read exactly one file, and do not read the other:

- `direct`: `${CLAUDE_PLUGIN_ROOT}/references/sync-direct.md`
- `qi`: `${CLAUDE_PLUGIN_ROOT}/references/sync-qi.md`

That file holds the status command, the states, pull, detach and attach, and the pipeline check for that mode. Not signed in (exit `2`): `/arcus:setup`.

## Never

- Edit `arcus.lock` or `.arcus/`, or push to get past a state.
- Push or run from here: hand over to `/arcus:push` or `/arcus:run`.
