# Arcus (Claude Code plugin)

Hooks-based capture of **Claude Code session context** for downstream systems (e.g. Testsigma): prompts, tool inputs/outputs (including large reads), subagent boundaries, stop/summary signals, and transcript paths.

## Install

This repo is **also a marketplace** (`.claude-plugin/marketplace.json` lists `arcus`).

**From GitHub (no clone):**

```bash
claude plugin marketplace add testsigmahq/arcus-claude-plugin
claude plugin install arcus@testsigma
```

**From a local clone (for development):**

```bash
git clone git@github.com:testsigmahq/arcus-claude-plugin.git
cd arcus-claude-plugin
claude plugin marketplace add ./
claude plugin install arcus@testsigma
```

`claude plugin list` should then show `arcus@testsigma` as enabled.

To update after a code change, bump `version` in `plugins/arcus/.claude-plugin/plugin.json` and run `claude plugin update arcus@testsigma`. To remove: `claude plugin uninstall arcus@testsigma && claude plugin marketplace remove testsigma`.

**Requirements:** Python **3.9+** on `PATH`. The plugin resolves the interpreter
itself (`python3`, then `python`, then the `py` launcher), so Windows installs —
where `python3` is usually a Microsoft Store alias rather than a real interpreter —
work without extra setup. On Windows, Claude Code's own Git Bash requirement
([Git for Windows](https://git-scm.com/downloads/win)) also covers this plugin.

## Authenticate

Capture only ships data once you log in:

```
/arcus:login        # SSO; stores refresh token in OS keychain. Run once per machine.
```

The command asks which region your Testsigma account is in before opening the
browser, because each region is a separate deployment and signing in to the
wrong one sends this session's captured data to the wrong place:

| Region | Key | API server | Auth server |
| --- | --- | --- | --- |
| United States (default) | `us` | `agentic-test.testsigma.com` | `arcus.testsigma.com` |
| India | `in` | `agentic-test-in.testsigma.com` | `arcus-in.testsigma.com` |
| Europe | `eu` | `agentic-test-eu.testsigma.com` | `arcus-eu.testsigma.com` |

The chosen region's hosts are written into the plugin's `config.json`, so every
later call — token refresh, project listing, event ingest — follows it
automatically. To switch, run `/arcus:logout` then `/arcus:login` again.

Regions are defined in `plugins/arcus/servers.json`, keyed by region rather than
suffixed per field, so a region cannot be half-configured with one host missing.
`resolve_region()` returns nothing for an unknown key rather than falling back to
a default host, so a typo fails loudly instead of authenticating elsewhere.

Until then hooks run as a **no-op** — nothing is sent remotely.

## Commands

| Command | Purpose |
| --- | --- |
| `/arcus:login` | Authenticate via SSO. Asks for your region, then stores the refresh token in your OS keychain. |
| `/arcus:logout` | Clear local credentials (server-side revoke not yet supported). |
| `/arcus:project list [search]` | List accessible Testsigma projects (optional substring filter). |
| `/arcus:project use <project_id>` | Pin a project; future events carry it. |
| `/arcus:project current` | Show the pinned project. |
| `/arcus:map ticket <KEY>` | Link a ticket (Jira / ADO / Linear / ClickUp / GitHub) to the session's workflow. |
| `/arcus:test [feature]` | Author Testsigma script e2e tests for this repo, validate them, and offer to run them. |
| `/arcus:push` | Push the test cases authored this session to Agentic Test; pick a sprint or leave unmapped (the `testsigma` CLI does the work). |
| `/arcus:help` | Show commands and typical flow. |

**Typical flow:** `/arcus:login` → `/arcus:project list` then `/arcus:project use <id>` → work on a branch (each session auto-resolves to a workflow) → `/arcus:map ticket <KEY>` → `/arcus:test` to author tests → `/arcus:push` to push them into a sprint.

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

Each hook POSTs to `{host}/api/v1/plugin/events` (host from `/arcus:login`). Read/Write/Edit file snapshots and large binaries (base64 images, long strings) are also captured and sent as attachments. Nothing is written to a local event log.

Per-session state lives under `$CLAUDE_PLUGIN_DATA/sessions/<session_id>/` (override with `TESTSIGMA_CONTEXT_DIR`) — a `session_manifest.json` (cwd, transcript, git/ticket grouping signals, Testsigma link) plus `attachments/` and `context_files/`.

## Privacy & data controls

Once you log in (`/arcus:login`), this plugin transmits your session — prompts, tool calls/inputs/outputs, and file contents it captures — to Testsigma. See the [Testsigma Privacy Policy](https://testsigma.com/privacy-policy) for what's collected and how it's handled. Until you log in, hooks are a no-op and nothing is sent.

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
arcus-claude-plugin/
├── .claude-plugin/marketplace.json   # marketplace manifest
└── plugins/arcus/                    # the plugin
    ├── .claude-plugin/plugin.json
    ├── commands/                     # /arcus:login, logout, map, project, help
    ├── hooks/hooks.json
    ├── scripts/                      # capture_hook, capture_sinks, auth/, map/, project/
    ├── tests/                        # pytest suite
    └── pyproject.toml
```

## Development

All commands run from `plugins/arcus/`.

```bash
pytest                 # test suite
ruff check .           # lint
ruff format .          # format
```

Supported on macOS, Linux and Windows, and on Python 3.9 and newer — the
scripts rely only on the standard library, with `keyring` used for refresh-token
storage when a backend is available and a mode-restricted file as the fallback.

### Cross-platform code

Anything that differs by operating system belongs in **`scripts/hostos.py`**, not
in a caller. It is the single place where a platform branch is allowed, and every
branch keys off a *capability* — does this module import, does this call succeed —
rather than an OS or Python version, so the same code runs from Windows 7 to 11
without version checks to keep current.

| Need | Use | Why not the obvious thing |
| --- | --- | --- |
| Lock a file across processes | `hostos.file_lock(path)` | `fcntl` does not exist on Windows; `msvcrt` locks are mandatory, so the lock goes in a `<path>.lock` sidecar and never in the file being truncated |
| Create a directory | `hostos.makedirs(path)` | Paths over 260 characters fail on Windows unless prefixed; returns `False` instead of raising into a hook |
| Open a deep path | `open(hostos.long_path(p), …)` | The `\\?\` prefix opts out of MAX_PATH on every Windows version, unlike the per-machine `LongPathsEnabled` flag |
| Build a path component | `hostos.safe_component(name)` | `nul`, `con`, `com1`… are reserved on Windows with or without an extension, and trailing dots and spaces are silently dropped |
| Owner-only file permissions | `hostos.restrict_file(path)` | `chmod(0o600)` only sets the read-only bit on Windows; an explicit ACL is required |
| Run a subprocess | `hostos.run_text(cmd)` | `text=True` decodes with the console codepage and raises `UnicodeDecodeError` on non-ASCII output; also resolves `.cmd` shims via PATHEXT |

Two rules the module cannot enforce for you:

- Use `os.replace()`, not `os.rename()`, for atomic writes — `os.rename()` fails
  on Windows when the destination already exists.
- Pass `encoding="utf-8"` explicitly to `open()`; the platform default is not
  UTF-8 on Windows.

### Launching Python

Hooks and slash commands never call `python3` directly. They go through
`scripts/arcus-py.cmd`, which resolves the interpreter at call time.

That file is a **polyglot**: `cmd.exe` runs the batch block, while a POSIX shell
reads the leading `:` as a no-op and swallows the block as a heredoc before
running the `sh` section underneath. One file therefore works whichever shell
Claude Code uses, on any OS. The pattern is borrowed from the `superpowers`
plugin's `run-hook.cmd`.

It exists because Windows has no `python3` on `PATH`: the python.org installer
ships `python.exe` and the `py` launcher, and the name `python3` is normally a
Microsoft Store app-execution alias that opens the Store and exits non-zero. So
each candidate is probed by *running* it — `command -v` alone would happily
accept the Store alias — and the first one reporting Python 3.9+ wins. When none
is found the launcher exits 0, so a missing interpreter disables capture instead
of breaking the session.

Two things worth knowing if you change it:

- The batch half uses `goto` labels rather than parenthesised blocks, because
  `%ERRORLEVEL%` inside a block is expanded when the block is *parsed*, not when
  it runs.
- Keep the name free of a `.sh` extension. Claude Code's Windows handling
  prepends `bash` to any command containing `.sh`, which would defeat the point.

A symlink cannot do this job: it only redirects which file is opened, and Windows
ignores shebangs, so it could never supply an interpreter — and Git checks
symlinks out as plain text files on Windows by default.

## Releasing

`plugins/arcus/.claude-plugin/plugin.json` is the **single source of truth** for
the version. Claude Code parses that manifest before any of this code runs, so
its `version` has to be a literal string — it is the one place the value cannot
be computed.

Everything else derives from it rather than keeping a copy:

- Python code calls `auth.config.plugin_version()`, which reads the manifest at
  runtime. Do not reintroduce a `PLUGIN_VERSION` constant; the one that used to
  live in `scripts/auth/cli.py` had silently drifted to `0.1.0`.
- `plugins/arcus/pyproject.toml` still carries a literal, because PEP 621
  requires one and this project declares no build backend that could compute it.
  That single remaining duplicate is guarded by a test, so drift fails CI rather
  than shipping.

To release, bump the manifest and `pyproject.toml` together, following semver:
patch for bug fixes, minor for new commands or hooks, major for anything that
breaks an existing install.

```bash
pytest tests/test_hostos.py -k version   # fails if the two disagree
```

## CI

`.github/workflows/ci.yml` runs on pushes to `dev` and `prod`, on pull requests
targeting either, and on demand via `workflow_dispatch`. It runs the suite on
Linux, macOS and Windows. Windows is
the point of the matrix: it is the only runner that exercises the `msvcrt`, ACL
and MAX_PATH branches of `hostos.py`, and it covers Python 3.9 through 3.13. A
separate job proves both halves of the `arcus-py.cmd` polyglot — under `cmd.exe`,
under POSIX `sh`, and under Git Bash — and runs one real hook event end to end.

## License

MIT — see [LICENSE](LICENSE).
