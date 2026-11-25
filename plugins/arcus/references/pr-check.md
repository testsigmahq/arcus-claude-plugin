# PR check: budgets, when to try to break it, and the local base

The details behind `/arcus:pr-check`. The skill says the order.

## When the break lane runs

| Signal | Then |
|---|---|
| `ARCUS_PR_CHECK_BREAK=off`, or the PR has the label `arcus:no-break` | Skip it. Say so in the report |
| `ARCUS_PR_CHECK_BREAK=on`, or the label `arcus:break` | Run it |
| Every changed file is documentation (`*.md`, `docs/`), a test (`*.test.*`, `__tests__/`, `e2e/`) or CI config | Skip it |
| Otherwise | Run it when the diff changes something a user can see: a screen, a route, a request the app makes, data it shows. Say in one line why |

## Budget

The run stops at whichever limit comes first, and says which.

| Level (`ARCUS_PR_CHECK_BUDGET`) | Time for the break lane | Scenarios written |
|---|---|---|
| `low` (default) | 20 minutes | 8 |
| `high` | 45 minutes | 20 |

The time counts from the break agent's first scenario to its last run on the change. The regression lane and the base runs are not
counted: they are bounded by the number of tests.

Order scenarios so the ones most likely to find something run first: what the diff changes that a user sees, then the
callers of the changed code, then the areas where past fixes cluster. When the budget runs out, the rest are listed in
the report as not run.

## A scenario

- One user goal per test, written as a user would do it, with a `verify` for each thing a user should see.
- Not a copy of a story case: the regression lane already runs those.
- Not about how the code is built (class names, internal state). The judge throws those out as test issues.
- Never shaped to fail. A scenario that passes is a scenario that found nothing.

## What counts

`node S diff` keeps a test only when it **failed on the PR's build and failed again on a re-run there, while the base
build passed or failed another way** (at another step, or with another message). A story test that was already broken
on the base can still show this PR breaking it earlier. Everything else is listed in the report and not judged:

- passed on both: the story's cases that held,
- failed the same way on the base: already broken, not this PR's,
- passed on the re-run: flaky,
- did not compile, or did not run on one side.

## The judge

The `pr-check-judge` subagent judges each difference from the story, its cases, the test, both outcomes and the failing
step's screenshot from each build, all of it in the packet `node S packets` writes. It has only a file reader and never
sees the diff or your session. The story is the issue's title and acceptance criteria as `arcus issue show` gives them.
Not seeing the code is a strong default, not a guarantee: keep its prompt to the packet path. Verdicts:
`real_bug`, `intended_change`, `test_issue`, `environment_issue`, `ambiguous`. A story case that is a real bug or
unclear blocks the merge. An intended change asks for the case to be updated in QI. The break lane never blocks; a
low-confidence bug there is reported as unclear.

## Before review, on the developer's stack

The only mode. It needs `ARCUS_PR_CHECK_SWITCH`. The story's tests pass, and the PR is a draft. The change and its base
are served at the same address, one after the other, because the app's sign-in is tied to one host. The repo's
recipe gives two commands:

- `ARCUS_PR_CHECK_SWITCH` serves the merge base, and returns once it answers.
- `ARCUS_PR_CHECK_RESTORE` serves the developer's branch again.

The switch checks out the merge base, so tracked files must be committed. The skill runs everything on the
change first (the story tests, then the break agent in the background), switches once for the base runs, and restores
right after, even when a run failed. While the break agent runs, the code must not change: the build under test is the
working tree.

Each real or unclear finding gets the developer's choice. A fixed one passes on a re-run on the change, and stops
blocking. A shipped one carries a one-line reason into the comment and is still pushed to QI as a pending case. A story
case shipped unfixed still blocks: CI re-runs the story's accepted tests, and it will fail.

The check's part of the comment is a section between `<!-- arcus-pr-check:v1 -->` and `<!-- /arcus-pr-check -->`. With a
"Ran locally" comment (marker `<!-- arcus:ran-locally -->`) on the PR, it goes into that comment, and a later run replaces it there.

## Environment

| Variable | Means |
|---|---|
| `ARCUS_PR_URL`, `ARCUS_BASE_URL` | Both the stack's address, which the repo's recipe gives |
| `ARCUS_ISSUE` | The issue key, from the trigger comment; else the branch, the commits or the PR title name it |
| `ARCUS_STACK_DIRS` | Other repos of the stack, checked out, colon-separated, to read |
| `ARCUS_PR_CHECK_BUDGET` | `low` or `high` |
| `ARCUS_PR_CHECK_BREAK` | `on` or `off` |
| `ARCUS_PR_CHECK_SWITCH` | Local mode: the repo recipe's command that serves the merge base |
| `ARCUS_PR_CHECK_RESTORE` | Local mode: the repo recipe's command that serves the developer's branch again |
| `ARCUS_PR_CHECK_RESET` | A command that puts the test data back, run before each run of the story tests |
| `ARCUS_PR_CHECK_PUSH` | `1` pushes real findings to QI as pending cases without asking |
