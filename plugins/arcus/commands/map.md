---
description: Map a ticket key to the current session's workflow (auto-routes to sprint)
---

Link a ticket (Jira / Azure DevOps / Linear / ClickUp / GitHub) to the workflow
resolved from this Claude session. Provider is auto-detected by the server from
sprint membership.

Subcommands:

- `/arcus:map ticket <KEY>` — map ticket key to current session's workflow

## Required pre-flight (do NOT skip)

Before running the map CLI, the agent MUST:

1. Read the pinned project by running:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/project/cli.py" current
   ```

2. If output is `(no project pinned; run /arcus:project use <id>)`, ABORT. Tell the user to pin a project first via `/arcus:project use <id>`. Do NOT execute the map command.
3. If a project is pinned, resolve its name with:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/project/cli.py" list
   ```

   then show the user the pinned project (id + name) and the ticket key, and ask for explicit confirmation.
4. Only after the user confirms, run the execute block below.

Confirmation is mandatory every invocation — even if the same ticket was mapped earlier in this session. Do NOT run the execute block on the first turn.

Execute (only after explicit user confirmation):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/map/cli.py" $ARGUMENTS
```
