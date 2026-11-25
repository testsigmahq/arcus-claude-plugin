# Catch: the settings, the budget, and what counts

The details behind `/arcus-jit:catch`. The skill says the order.

## The settings: `arcus-jit.json`

One file per test folder, next to `arcus.json`, committed with the repo. It holds how this repo serves its base and how
it wants catching done. It never holds a secret.

```json
{
  "url": "http://dev-arcus.testsigma.com",
  "base": {
    "serve": "./jit-base.sh base",
    "restore": "./.arcus/jit/jit-base.sh back",
    "branch": "dev"
  },
  "vars": { "email": "ARCUS_E2E_EMAIL", "password": "ARCUS_E2E_PASSWORD" },
  "reset": "",
  "budget": "low",
  "catch": "auto",
  "rubric": "",
  "read": []
}
```

| Key | Means |
|---|---|
| `url` | The address the change, and then the base, are served at on the developer's stack |
| `base.serve` | The repo's command that serves the merge base in place of the change, and returns once `url` answers |
| `base.restore` | The command that serves the developer's branch again |
| `base.branch` | The branch the merge base is taken from (the PR's base branch) |
| `vars` | `--var` names for the runs, each mapped to the environment variable that holds its value |
| `reset` | A command that puts the test data back, run before each run of the story tests. Empty: none |
| `budget` | `low` or `high` |
| `catch` | `auto` (the rules below), `on` or `off` |
| `rubric` | A markdown file, relative to this folder, that the judge reads with every packet: what this team counts as a bug |
| `read` | Other repos of the stack, checked out, that the writer may read |

A team that wants something other than these knobs allow (another lane, another bar, another judge) writes its own
skill on the Arcus CLI. This plugin is one way to catch, not the only one.

## When the catch lane runs

| Signal | Then |
|---|---|
| `catch` is `off`, or the PR has the label `arcus:no-catch` | Skip it. Say so in the report |
| `catch` is `on`, or the label `arcus:catch` | Run it |
| Every changed file is documentation (`*.md`, `docs/`), a test (`*.test.*`, `__tests__/`, `e2e/`) or CI config | Skip it |
| Otherwise | Run it when the diff changes something a user can see: a screen, a route, a request the app makes, data it shows. Say in one line why |

## Budget

The writer stops at whichever limit comes first, and says which.

| `budget` | Time for the catch lane | Catching tests written |
|---|---|---|
| `low` (default) | 20 minutes | 8 |
| `high` | 45 minutes | 20 |

The time counts from the writer's first test to its last run on the change. The regression lane and the base runs are
not counted: the number of tests bounds them.

## A catching test

- One user goal per test, written as a user would do it, with a `verify` for each thing a user should see.
- Not a copy of a story case: the regression lane already runs those.
- Not about how the code is built (class names, internal state). The judge throws those out as test issues.
- Never shaped to fail. One that passes caught nothing.

## What counts

`node S diff` keeps a test only when it **failed on the change and failed again on a re-run there, while the base passed
or failed another way** (at another step, or with another message). Everything else is listed in the report and not
judged:

- passed on both: the story's cases that held,
- failed the same way on the base: already broken, not this change's,
- passed on the re-run: flaky,
- did not compile, or did not run on one side.

## The judge

The `catch-judge` subagent judges each difference from the story, its cases, the test, both outcomes, the failing
step's screenshot from each build and the team's rubric, all in the packet `node S packets` writes. It has only a file
reader and never sees the diff or your session. The story is the issue's title and acceptance criteria as `arcus issue
show` gives them. Not seeing the code is a strong default, not a guarantee: keep its prompt to the packet path.

Verdicts: `real_bug`, `intended_change`, `test_issue`, `environment_issue`, `ambiguous`. A story case that is a real bug
or unclear blocks the merge. An intended change asks for the case to be updated in QI. A catch never blocks; a
low-confidence bug there is reported as unclear.

## The base, on the developer's stack

The change and its base are served at the same address one after the other, because an app's sign-in is often tied to
one host. `base.serve` checks out the merge base, so tracked files must be committed. The skill runs everything on the
change first (the story tests, then the writer in the background), serves the base once for the base runs, and restores
right after, even when a run failed. While the writer runs, the code must not change: the build under test is the
working tree.

## Fix or ship

Each real or unclear difference gets the developer's choice. A fixed one passes on a re-run on the change, and stops
blocking. A shipped one carries a one-line reason into the comment; a shipped catch is still pushed to QI as a pending
case. A story case shipped unfixed still blocks.

## The comment

The check's part is a section between `<!-- arcus-jit:catch:v1 -->` and `<!-- /arcus-jit:catch -->`. With a "Ran
locally" comment (marker `<!-- arcus:ran-locally -->`) on the PR, it goes into that comment, and a later run replaces it
there.
