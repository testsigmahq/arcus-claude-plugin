# Manual smoke — testsigma-tests

Prerequisite: `testsigma` CLI installed with `code reference`/`code examples`
(Component 1), and the arcus plugin updated to >= 0.3.0. Steps 2–4 additionally
need a CLI build whose `code run` supports web targets (branches on the compiled
`applicationType`); older builds demand `--device` for every run.

1. In a sample **web** repo, run `/arcus:test login`.
   - Expect: the skill detects `web`, runs `testsigma code reference --type web`
     and `testsigma code examples --type web`, writes `tests/testsigma/login.spec.ts`,
     and runs `testsigma code validate --input tests/testsigma/login.spec.ts` to a
     clean result.
   - Expect: it then confirms the spec's `page.goto(...)` URL is reachable, and
     warns that a real browser window will open, before any `testsigma code run` —
     it must NOT run unprompted.
2. On "yes" to the web run:
   - Expect: a visible browser window opens (headed by default) and it is the
     machine's **installed** Chrome, not a downloaded Chromium. Verify mid-run with
     `ps -Ao command= | grep "Google Chrome.app/Contents/MacOS"` — the command line
     must show that path and must NOT contain `--headless`.
   - Expect: no `--device` prompt, no Appium requirement.
   - Expect: a single JSON summary line with `overall` and `counts`.
3. Confirm a deliberately wrong assertion yields `overall: "failed"` and that the
   failing step in `resultsFile` carries `errorType`, `message`, and `locator`.
4. Confirm `--headless` suppresses the window and `--browser edge` drives installed
   Edge, both still passing.
5. Confirm a **mobile** spec still requires `--device` and rejects an id that is not
   connected — the web path must not have loosened the mobile gate.
6. Confirm `testsigma --version` failing (CLI absent) makes the skill STOP at
   preflight with install guidance.
7. Confirm an ambiguous repo (both web and mobile signals) makes the skill ASK for
   the type instead of guessing.
8. Confirm a run with the local agent stopped fails with "Could not reach the local
   agent" and the skill asks the developer to start it — for web as well as mobile.

Record pass/fail for each here when run.
