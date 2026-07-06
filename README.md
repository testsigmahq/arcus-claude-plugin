# Atto (Claude Code plugin)

Hooks-based capture of **Claude Code session context** for downstream systems (e.g. Testsigma): prompts, tool inputs/outputs (including large reads), subagent boundaries, stop/summary signals, and transcript paths.

## Install

This repo is **also a marketplace** (`.claude-plugin/marketplace.json` lists `atto`).

**From GitHub (no clone):**

```bash
claude plugin marketplace add testsigmahq/atto-claude-plugin
claude plugin install atto@testsigma
```

**From a local clone (for development):**

```bash
git clone git@github.com:testsigmahq/atto-claude-plugin.git
cd atto-claude-plugin
claude plugin marketplace add ./
claude plugin install atto@testsigma
```

`claude plugin list` should then show `atto@testsigma` as enabled.

To update after a code change, bump `version` in `plugins/atto/.claude-plugin/plugin.json` and run `claude plugin update atto@testsigma`. To remove: `claude plugin uninstall atto@testsigma && claude plugin marketplace remove testsigma`.

**Requirements:** Python **3.9+** on `PATH` as `python3` (standard on macOS/Linux).

## Authenticate

Capture only ships data once you log in:

```
/atto:login        # SSO; stores refresh token in OS keychain. Run once per machine.
```

Until then hooks run as a **no-op** — nothing is sent remotely.

## Commands

| Command | Purpose |
| --- | --- |
| `/atto:login` | Authenticate via SSO. Stores refresh token in OS keychain. |
| `/atto:logout` | Clear local credentials (server-side revoke not yet supported). |
| `/atto:project list [search]` | List accessible Testsigma projects (optional substring filter). |
| `/atto:project use <project_id>` | Pin a project; future events carry it. |
| `/atto:project current` | Show the pinned project. |
| `/atto:map ticket <KEY>` | Link a ticket (Jira / ADO / Linear / ClickUp / GitHub) to the session's workflow. |
| `/atto:test [feature]` | Author Testsigma script e2e tests for this repo, validate them, and offer to run them. |
| `/atto:push` | Push the test cases authored this session to Agentic Test; pick a sprint or leave unmapped (the `testsigma` CLI does the work). |
| `/atto:help` | Show commands and typical flow. |

**Typical flow:** `/atto:login` → `/atto:project list` then `/atto:project use <id>` → work on a branch (each session auto-resolves to a workflow) → `/atto:map ticket <KEY>` → `/atto:test` to author tests → `/atto:push` to push them into a sprint.

## What gets captured

| Hook | Captured |
| --- | --- |
| SessionStart | `session_id`, `cwd`, `transcript_path`, start reason |
| UserPromptSubmit | Raw user prompt |
| Pre/PostToolUse | Tool name, input, and `tool_response` (e.g. full Read content) |
| PostToolUseFailure | Tool errors |
| Subagent Start/Stop | Subagent id/type; agent transcript path |
| Stop / StopFailure | Last assistant message or API error |
| SessionEnd | Exit reason |

Each hook POSTs to `{host}/api/v1/plugin/events` (host from `/atto:login`). Read/Write/Edit file snapshots and large binaries (base64 images, long strings) are also captured and sent as attachments. Nothing is written to a local event log.

Per-session state lives under `$CLAUDE_PLUGIN_DATA/sessions/<session_id>/` (override with `TESTSIGMA_CONTEXT_DIR`) — a `session_manifest.json` (cwd, transcript, git/ticket grouping signals, Testsigma link) plus `attachments/` and `context_files/`.

## Privacy & data controls

**Sensitive files are always blocked** regardless of settings — `.env*`, private keys (`*.pem`/`*.key`/`*.p12`/`*.jks`), `credentials*`, `service-account*.json`, `.netrc`, `.pgpass`, and anything under `~/.ssh`, `~/.gnupg`, `~/.aws/credentials`, `~/.gcloud/legacy_credentials`. Blocked files are sent as `{skipped: true, reason: 'sensitive_path'}`.

**Noise dirs are excluded from capture** — files under dependency, build, and VCS directories are never snapshotted or sent. Built-in list:

```
node_modules  bower_components  jspm_packages  .pnp  .yarn
.next  .nuxt  .svelte-kit  .angular  .astro  .expo  .docusaurus
.cache  .parcel-cache  .turbo  .vite  .webpack
dist  build  out  .output  coverage  .nyc_output
.venv  venv  __pycache__  .mypy_cache  .pytest_cache  .ruff_cache  .tox  .eggs  *.egg-info
target  vendor  .gradle  .mvn
.terraform  .serverless
Pods  Carthage  DerivedData
.git  .hg  .svn  .idea  .vscode
```

Env-var toggles (accept `true`/`false`/`yes`/`no`/`1`/`0`):

| Variable | Default | Effect |
| --- | --- | --- |
| `TESTSIGMA_CONTEXT_INCLUDE_FILES` | `true` | Send attachment bytes; `false` = manifest metadata only |
| `TESTSIGMA_DISABLE_CONTEXT_FILE_SNAPSHOTS` | unset | `true` skips local `context_files/` snapshots |
| `TESTSIGMA_SENSITIVE_PATTERNS` | unset | Comma-separated globs added to the sensitive denylist |
| `TESTSIGMA_EXCLUDE_PATTERNS` | unset | Comma-separated globs added to the noise-exclusion list |

Additional tuning knobs (attachment size caps, webhook retries/timeout, blob externalization threshold) are documented inline in `scripts/capture_hook.py` and `scripts/capture_sinks.py`.

## How it works

Events are normalized in `scripts/capture_hook.py`, then run through a sink pipeline in `scripts/capture_sinks.py` (`ManifestSink` updates the local manifest; `WebhookSink` POSTs to ingest and writes back the returned `workflow_id`/`context_id`). To add a backend, implement `ContextCaptureSink` and extend `build_default_sinks()`. See `scripts/testsigma_session_link.py` for the session↔workflow linking.

Hooks fail safe — a capture error never blocks the Claude Code session.

## Repo layout

```
atto-claude-plugin/
├── .claude-plugin/marketplace.json   # marketplace manifest
└── plugins/atto/                    # the plugin
    ├── .claude-plugin/plugin.json
    ├── commands/                     # /atto:login, logout, map, project, help
    ├── hooks/hooks.json
    ├── scripts/                      # capture_hook, capture_sinks, auth/, map/, project/
    ├── tests/                        # pytest suite
    └── pyproject.toml
```

## License

MIT — see [LICENSE](LICENSE).
