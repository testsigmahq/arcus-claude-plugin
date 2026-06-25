---
description: Push the test cases you authored this session to Agentic Test (pick a sprint, or leave unmapped)
---

Push the Testsigma-script test cases authored in this Claude session — the
`*.spec.ts` files written or edited under `tests/` — into Agentic Test.

Authentication, session detection, compilation, and the Agentic Test calls all
happen in the `testsigma` CLI. This command only helps you pick a target. It does
**not** read files, compile, or handle auth itself.

## Required pre-flight (do NOT skip)

1. Read the pinned project:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/project/cli.py" current
   ```

2. If the output is `(no project pinned; run /atto:project use <id>)`, ABORT. Tell
   the user to pin a project first with `/atto:project use <id>`. Do NOT continue.

## Choose a target

3. List the project's sprints (substitute the pinned project id from step 1):

   ```bash
   testsigma sprints list --project-id <pinned_project_id>
   ```

   If this fails with an authentication error, tell the user to run `testsigma login`
   (the CLI uses its own login, separate from `/atto:login`).

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

## Push (only after the user picks)

6. Run exactly one of:

   ```bash
   testsigma code push --sprint <work_cycle_id> --issue <issue_key>
   ```

   or

   ```bash
   testsigma code push --unmapped
   ```

   Do **not** pass `--session-id` — the CLI auto-detects the current session. Do
   **not** pass `--project-id` — the server derives the project from the target.
   If the CLI reports an invalid issue (HTTP 422), re-run `testsigma sprints issues`
   to show valid `ISSUE_KEY`s and ask the user to pick again.

7. Report back the per-test-case results the CLI prints (each line is
   `created` or `updated`, with the test case name and id). If the CLI reports
   "Nothing to push," tell the user no changed `*.spec.ts` files were found in this
   session — they may need to author tests first (see `/atto:test`).
