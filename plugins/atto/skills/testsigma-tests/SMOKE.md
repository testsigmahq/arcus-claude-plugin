# Manual smoke — testsigma-tests

Prerequisite: `testsigma` CLI installed with `code reference`/`code examples`
(Component 1), and the atto plugin updated to >= 0.3.0.

1. In a sample **web** repo, run `/atto:test login`.
   - Expect: the skill detects `web`, runs `testsigma code reference --type web`
     and `testsigma code examples --type web`, writes `tests/testsigma/login.spec.ts`,
     and runs `testsigma code validate --input tests/testsigma/login.spec.ts` to a
     clean result.
   - Expect: it then asks for a base URL before any `testsigma code run` — it must
     NOT run unprompted.
2. Confirm `testsigma --version` failing (CLI absent) makes the skill STOP at
   preflight with install guidance.
3. Confirm an ambiguous repo (both web and mobile signals) makes the skill ASK for
   the type instead of guessing.

Record pass/fail for each here when run.
