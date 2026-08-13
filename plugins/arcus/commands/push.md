---
description: Push the test cases you authored this session to Arcus (pick a sprint, or leave unmapped)
---

Push the Testsigma-script test cases authored in this Claude session — the
`*.spec.ts` files written or edited under `tests/` — into Arcus.

Authentication, session detection, compilation, and the Arcus calls all
happen in the `testsigma` CLI. This command only helps you gather the target and
metadata the CLI needs. It does **not** read files, compile, or handle auth itself.

## Required pre-flight (do NOT skip)

1. Read the pinned project:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/project/cli.py" current
   ```

2. If the output is `(no project pinned; run /arcus:project use <id>)`, ABORT. Tell
   the user to pin a project first with `/arcus:project use <id>`. Do NOT continue.

   Otherwise capture the printed project id as `<project_id>` — every command below
   needs it.

## Choose a target

3. List the project's sprints:

   ```bash
   testsigma sprints list --project-id <project_id>
   ```

   If this fails with an authentication error, tell the user to run `testsigma login`
   (the CLI uses its own login, separate from `/arcus:login`).

4. Show the user the sprints (`WORK_CYCLE_ID` + `TITLE`) and also offer an
   **"unmapped"** option (store under this session's unmapped Claude-conversation
   entity). Ask the user to choose exactly one. Do NOT guess a default.

5. If the user picked a sprint, list that sprint's Jira stories and have them pick one:

   ```bash
   testsigma sprints issues --sprint <work_cycle_id>
   ```

   Show the `ISSUE_KEY` + `TITLE` and ask the user to pick exactly one story. The
   chosen `ISSUE_KEY` is required for a sprint push — without it the test cases are
   pushed without a story link and will not appear under any story in the UI.

## Choose a module (REQUIRED for every push)

6. Every pushed test case must be stamped with a product module. List the project's
   modules:

   ```bash
   testsigma modules list --project-id <project_id>
   ```

   Show the user the `MODULE_ID` + `NAME` (+ `SLUG`) rows and ask them to pick exactly
   one. Pass the chosen `MODULE_ID` as `--module`. If none fits, the user may instead
   give a **new module name** — `--module <name>` creates it on the fly. Do NOT guess
   a module; `--module` is mandatory and the push fails without it.

## Optional metadata (offer, then include when set)

7. **Priority** — ask whether to set a priority (`High` / `Medium` / `Low`). Pass it
   as `--priority <name>`. If the user doesn't care, omit the flag (the server
   defaults to `Medium`).

8. **Test type** — list the account's test types and ask the user to pick one:

   ```bash
   testsigma test-types list
   ```

   Show the `NAME` rows. Default to **Functional** — a pushed test case is
   functional validation, not a unit test — and pass the choice as
   `--test-type <name>`. Omitting the flag also yields Functional, so only pass it
   when the user picks something else.

9. **Run status** — if the tests were run this session (e.g. via `/arcus:test`, which
   reports an overall `passed`/`failed`), pass the result as `--run-status Passed`
   or `--run-status Failed` so each test case records its last code-run result. It
   accepts only `Passed` or `Failed`; **omit** the flag entirely if the tests were
   not run.

## Push (only after the user has picked target + module)

10. Build one command with every applicable flag. Use the sprint form:

   ```bash
   testsigma test push \
     --project-id <project_id> \
     --sprint <work_cycle_id> \
     --issue <issue_key> \
     --module <module_id_or_name> \
     [--priority <High|Medium|Low>] \
     [--test-type <name>] \
     [--run-status <Passed|Failed>]
   ```

   or the unmapped form:

   ```bash
   testsigma test push \
     --project-id <project_id> \
     --unmapped \
     --module <module_id_or_name> \
     [--priority <High|Medium|Low>] \
     [--test-type <name>] \
     [--run-status <Passed|Failed>]
   ```

   Rules:
   - `--project-id` is **required** for both `--sprint` and `--unmapped`.
   - `--module` is **required** for every push.
   - `--sprint` and `--unmapped` are mutually exclusive; `--issue` is sprint-only
     (it cannot be combined with `--unmapped`).
   - Do **not** pass `--session-id` — the CLI auto-detects the current session.
   - Do **not** pass `--input` — omit it so the CLI pushes exactly the `*.spec.ts`
     files authored/changed in this session. (Only pass `--input <comma,separated>`
     if the user explicitly wants to push specific files instead.)
   - Drop any bracketed `[--flag]` above that the user chose not to set.
   - If the CLI reports an invalid issue (HTTP 422), re-run `testsigma sprints issues`
     to show valid `ISSUE_KEY`s and ask the user to pick again.

10. Report back the per-test-case results the CLI prints (each line is `created` or
    `updated`, with the test case name and id). If the CLI reports "Nothing to push,"
    tell the user no changed `*.spec.ts` files were found in this session — they may
    need to author tests first (see `/arcus:test`).
