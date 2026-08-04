# Manual smoke — testsigma-tests

Prerequisite: `testsigma` CLI installed with `code reference`/`code examples`
(Component 1), and the arcus plugin updated to >= 0.3.0. Steps 2–6 also need a CLI
whose `code run` supports web targets and an agent serving `GET /browsers`.

1. In a sample **web** repo, run `/arcus:test login`.
   - Expect: the skill detects `web`, runs `testsigma code reference --type web`
     and `testsigma code examples --type web`, writes `tests/testsigma/login.spec.ts`,
     and runs `testsigma code validate --input tests/testsigma/login.spec.ts` to a
     clean result.
   - Expect: it then confirms the spec's `page.goto(...)` URL and warns that a
     browser window will open, before any `testsigma code run` — it must NOT run
     unprompted.
2. Confirm `testsigma list browsers --local` shows the same browsers the platform
   lists for this agent, each with a version and engine.
3. On "yes" to the web run, confirm a visible window opens and it is the binary the
   agent reported: `ps -Ao command= | grep -i chrome` shows that path, without
   `--headless`.
4. Confirm a deliberately wrong assertion yields `overall: "failed"` and that the
   failing step in `resultsFile` carries `errorType`, `message`, and `locator`.
5. Confirm `--headless` suppresses the window, and `--browser cft` launches Chrome
   for Testing from `<rootDir>/browsers/`.
6. Confirm `--browser opera` fails before launching anything, listing what is
   available.
7. Confirm a **mobile** spec still requires `--device` and rejects an unconnected
   id — the web path must not have loosened the mobile gate.
8. Confirm `testsigma --version` failing (CLI absent) makes the skill STOP at
   preflight with install guidance.
9. Confirm an ambiguous repo (both web and mobile signals) makes the skill ASK for
   the type instead of guessing.
10. Confirm a run with the agent stopped fails with "Could not reach the local
    agent", for web as well as mobile.

Record pass/fail for each here when run.
