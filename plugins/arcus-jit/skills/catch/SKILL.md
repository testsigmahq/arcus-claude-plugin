---
name: catch
description: Use when a developer wants their change caught before review - checked against its merge base and tried with new tests written to break it ("catch CW-412", "check this change before review", "try to break it"). Runs on the developer's own stack once the story's tests pass. Runs the story's tests on the change and the base, has a fresh-session agent write catching tests, keeps only what fails on the change alone, has a judge subagent rule on each against the story, records the developer's fix-or-ship choice, and writes one PR comment. Never edits a story test, never accepts.
---

# Catch: compare the change with its base, and try to break it

Just-in-time catching tests, after Meta's JiTTesting: tests written for one change, meant to fail if the change broke
something, judged before a person is asked. Two lanes, both in one PR comment:

- **Regression.** The story's own tests: the files `arcus issue show` names for its cases. Run this once they pass on
  the change (`/arcus:verify`). A story case that breaks blocks the merge, unless the developer fixes it.
- **Catch.** New tests a separate agent writes to find what the change broke that no case covers. A failing one is a
  catch. Advisory.

You never write the catching tests and never make the verdicts. The `catch-writer` subagent writes them in a fresh
session; the `catch-judge` subagent rules on each difference from the story and screenshots, never the diff. Hand each
only what this skill says. Budgets, the settings and what counts are in `${CLAUDE_PLUGIN_ROOT}/references/catch.md`.

`S` below is `${CLAUDE_PLUGIN_ROOT}/scripts/catch.mjs`, run with `node`. Keep every file this run writes under
`.arcus/jit/` (the work folder, `W`), except catching tests, which `arcus test run` needs in the project's `tests/`.

## 1. Settings and setup

Read `arcus-jit.json` next to `arcus.json`. Missing, or no `base.serve` and `base.restore`: the repo has no base recipe.
Stop and say so. Never compare with a deployed environment, and never run this in CI.

Tracked files must be committed (`git diff --quiet HEAD`), because `base.serve` checks out the merge base. Not clean:
stop and ask the developer to commit. Check `url` answers (`curl -sS -o /dev/null -w '%{http_code}' <url>`). Then
`/arcus:setup`'s checks: the CLI, the sign-in, `arcus browser list`, `web` in the platforms, and qi mode.

Every run below passes `--var <name>="$<ENV>"` for each entry of `vars`. The settings name environment variables,
never values; never write a value into a command you show.

## 2. The story and the PR

The issue key: the argument, else the branch name, the commit messages, the PR title. Stop at the first; say where.

```
arcus issue show <key> --json > W/issue.json
```

No key anywhere: go on without a story, and the comment says none was linked. Never pick a story yourself.

`gh pr view --json number,url,isDraft`. None: show the developer `gh pr create --draft --fill` and run it after their
yes. A PR that is not a draft: say it is already in review.

## 3. Regression lane, on the change

```
node S story-tests --issue W/issue.json
node S run --url <url> [--var ...] <files> > W/regression-pr.json
node S run --url <url> [--var ...] <failed files> > W/regression-retry.json
```

It lists only files this checkout has. None: the comment says "no automated tests for this story yet". With `reset`
set, run it before every run of the story tests. Never fix, edit or weaken a story test.

## 4. Catch lane

Decide whether it runs, as the reference says, and say why. Then start the `catch-writer` subagent in the background,
and tell the developer the check runs on the working tree, so the code must not change until it says it is done. Its
prompt holds only: the issue key, `W`, the merge base (`git merge-base origin/<base.branch> HEAD`), `url`, the `--var`
flags as you would type them, the story test files, the budget, the `read` folders, and `S`. Never your own view of the
change. When it is done it has written `W/catch-candidates.json`, `W/catch-pr.json`, `W/catch-retry.json` and
`W/stats.json`.

## 5. The base

Run `base.serve` and wait until `url` answers. It fails or `url` never answers: run `base.restore`, stop, and say
what it printed. Never move files, change git flags or pass other settings to get past it. Then, after `reset` if set:

```
node S run --url <url> [--var ...] <story test files> > W/regression-base.json
node S run --url <url> [--var ...] <candidate files> > W/catch-base.json
```

Run `base.restore` right after, even when a run failed, and check `url` answers again.

## 6. Judge

```
node S diff --lane regression --pr W/regression-pr.json --base W/regression-base.json --retry W/regression-retry.json --issue W/issue.json > W/regression.json
node S diff --lane catch --pr W/catch-pr.json --base W/catch-base.json --retry W/catch-retry.json > W/catch.json
node S packets --issue W/issue.json --out W/judge --diff W/regression.json --diff W/catch.json [--rubric <rubric>] > W/packets.json
```

Pass `--rubric` when the settings name one. For each packet, start `catch-judge` with only: `Judge the difference in
<packet path>.` Run them in parallel. Write their answers, in packet order, as a JSON array to `W/verdicts.json`; an
answer that is not one JSON object goes in as it is and counts as unclear. Never change, drop or argue with a verdict.

## 7. Fix or ship

Show every difference the judge called `real_bug` or `ambiguous`: the title, the verdict and reason, and where its
screenshots are. For each, ask the developer: fix it, or ship it with a one-line reason.

- **Fix**: the developer or their agent changes the app's code. Re-run that test on the change; it passes: `fixed`. It
  still fails: ask again. Never change the test to make it pass.
- **Ship**: record the reason as they wrote it. A story case shipped unfixed still blocks the merge.

Write `W/decisions.json`: `[{"n": <packet number>, "choice": "fixed"}, {"n": ..., "choice": "shipped", "reason": "..."}]`.

## 8. Report and comment

```
node S report --issue W/issue.json --pr-url <url> --base-url <url> --diff W/regression.json --diff W/catch.json --verdicts W/verdicts.json --decisions W/decisions.json --stats W/stats.json --local --comment W/comment.md > W/report.json
```

Find the PR's comment that starts with `<!-- arcus:ran-locally -->` or `<!-- arcus-jit:catch:v1 -->`, save its body to
`W/current.md`, and build the new body:

```
gh api repos/<owner/name>/issues/<n>/comments --paginate --jq '.[] | select(.body | startswith("<!-- arcus:ran-locally -->") or startswith("<!-- arcus-jit:catch:v1 -->")) | {id, body}'
node S splice --section W/comment.md --into W/current.md > W/body.json
```

Write `body` from `W/body.json` to `W/body.md`. Show it, and after a yes edit that comment (`gh api -X PATCH
repos/<owner/name>/issues/comments/<id> -F body=@W/body.md`) or add one (`gh pr comment <n> -R <owner/name> --body-file
W/body.md`). A later run edits it with no new yes. No PR or no `gh`: print it.

## 9. Catches become pending tests

Every catch judged `real_bug`, fixed or shipped, is a test worth keeping. Hand those files to `/arcus:push` as new cases
(`arcus test push <files> --new`, after step 2's `arcus issue show`): they land in QI as pending cases on the story, for
a person to accept. Its dry run and its yes apply. Never pass `--accept`, and never run `arcus test accept`.

Then delete every `catch-*.sigma` file and any element this run created that was not pushed. Never commit them.

## 10. Say

The story, the regression result, the catching tests written and what they caught, each decision, the conclusion, the
comment's link, what was pushed, and what did not run and why. If no story case still blocks, offer `gh pr ready <n>`
and run it only after a yes.

## What this skill never does

- Edit a story test or a case's expected result, or weaken a catching test.
- Write catching tests itself, or give the writer or the judge more than this skill says. Change or drop a verdict.
- Record a choice the developer did not make, or call a catch fixed before its test passes on the change.
- Serve the base without a clean tree, work around a failed `base.serve`, or leave the base serving.
- Run against an address the settings do not name, or guess one.
- Create a PR, post, push or mark ready without a yes.
- Accept anything, sign in, or start the agent or the app.
- Commit catching tests, or leave them in `tests/`.
