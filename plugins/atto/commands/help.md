---
description: Show Atto commands and how to use them
---

Atto captures Claude Code session context (prompts, tool I/O, file snapshots, subagent boundaries) and ingests it into Testsigma. Sessions are grouped by git branch and linked to a Testsigma workflow; you pick the project and map tickets.

## Commands

- `/atto:login` — Authenticate via SSO. Stores refresh token in OS keychain. Run once per machine.
- `/atto:logout` — Clear local credentials. Server-side revoke not yet supported.
- `/atto:project list [search]` — List Testsigma projects you can access. Optional substring filter.
- `/atto:project use <project_id>` — Pin a project. Future events tag this project.
- `/atto:project current` — Show pinned project.
- `/atto:map ticket <KEY>` — Link ticket (Jira / ADO / Linear / ClickUp / GitHub) to the workflow resolved from this session. Provider auto-detected from sprint membership.
- `/atto:test [feature]` — Author Testsigma script e2e tests for this repo, validate them, and offer to run them.
- `/atto:push` — Push the test cases authored this session to Agentic Test; pick a sprint or leave unmapped. The `testsigma` CLI does the work.

## Typical flow

1. `/atto:login` — once per machine.
2. `/atto:project list` then `/atto:project use <id>` — pick where sessions land.
3. Start working on a branch. Each Claude session resolves to a workflow automatically.
4. `/atto:map ticket <KEY>` — link ticket to the workflow when you know it.
5. `/atto:test` to author tests, then `/atto:push` to push them into a sprint.

## Where data lives

Per session: `$CLAUDE_PLUGIN_DATA/sessions/<session_id>/`
- `session_manifest.json` — grouping keys (branch, git user, ticket IDs) + `testsigma` link block
- `context_files/` — Read/Write/Edit snapshots mirroring project tree
- `attachments/` — binary payloads + dup of context_files

Hook events POST to `{chitragupt_host}/api/v1/plugin/events` (host from `/atto:login`).

## Troubleshooting

- Browser didn't open on login → copy URL from stderr, paste manually. Flow times out after 5 min.
- Events not ingesting → check `/atto:project current` is set and login still valid (re-run `/atto:login`).
- Wrong workflow linked → re-run `/atto:map ticket <KEY>` with correct ticket.
