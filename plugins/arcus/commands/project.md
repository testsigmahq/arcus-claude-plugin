---
description: List Arcus projects and pin the active project
---

Manage which Arcus project this plugin tags new events with. The
workflow inside Arcus is resolved automatically per session/branch —
you only need to pick a project.

Subcommands:

- `/arcus:project list [search]` — list projects (optional substring search)
- `/arcus:project use <project_id>` — pin a project; future events carry it
- `/arcus:project current` — show the pinned project

Execute:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/arcus-py.cmd" "${CLAUDE_PLUGIN_ROOT}/scripts/project/cli.py" $ARGUMENTS
```
