---
description: List Testsigma projects and pin the active project for Atto
---

Manage which Testsigma project this plugin tags new events with. The
workflow inside Testsigma is resolved automatically per session/branch —
you only need to pick a project.

Subcommands:

- `/atto:project list [search]` — list projects (optional substring search)
- `/atto:project use <project_id>` — pin a project; future events carry it
- `/atto:project current` — show the pinned project

Execute:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/project/cli.py" $ARGUMENTS
```
