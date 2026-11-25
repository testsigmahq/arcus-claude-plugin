---
name: pr-check
description: Use when a change should be checked against its base and someone should try to break it, on the developer's machine once the story's tests pass ("check this change", "pr-check CW-412", "try to break it before review"). Runs the story's tests on the change and the base build, has a fresh-session agent write scenarios to break the change, keeps only what fails on the change alone, has a judge subagent rule on each against the story, records the developer's fix-or-ship choice, and writes one PR comment. Never edits a story test, never accepts.
---

# PR check: compare the change with its base, and try to break it

Two lanes, both reported in one comment:

- **Regression.** The story's own tests, the files `arcus issue show` names for its cases. Run this check once they
  pass on the change (`/arcus:verify`). A story case that breaks blocks the merge, unless the developer fixes it first.
- **Break it.** New scenarios a separate agent writes to find what the change broke that no case covers. Advisory.

You never write the scenarios and never make the verdicts. The `pr-check-breaker` subagent writes scenarios in a fresh
session. The `pr-check-judge` subagent rules on each difference from the story and screenshots, never the diff. Hand each
only what this skill says. Budgets, the modes and the environment are in `${CLAUDE_PLUGIN_ROOT}/references/pr-check.md`.

`S` below is `${CLAUDE_PLUGIN_ROOT}/scripts/pr-check.mjs`, run with `node`. Keep every file this run writes under
`.arcus/pr-check/` (the work folder, `W`), except scenario tests, which `arcus test run` needs in the project's `tests/`.

## 1. Mode and setup

- **Local** (`ARCUS_PR_CHECK_SWITCH` is set, from the repo's recipe): the change and its base run one after the other on
  the developer's own stack, at one address (`ARCUS_PR_URL` = `ARCUS_BASE_URL`). You also need `ARCUS_PR_CHECK_RESTORE`.
  Tracked files must be committed (`git diff --quiet HEAD`): the switch checks out the merge base. Not clean: stop and
  ask the developer to commit.
- No `ARCUS_PR_CHECK_SWITCH`: the repo has no base recipe yet. Stop and say so. Never compare with a deployed
  environment, and never run this in CI.

Check each address answers (`curl -sS -o /dev/null -w '%{http_code}' <url>`). Never guess one. Then `/arcus:setup`'s
checks: the CLI, the sign-in, `arcus browser list`, `web` in the platforms, and qi mode (`arcus project mode show`).

## 2. The story and the PR

Find the issue key, and stop at the first: `ARCUS_ISSUE`, the branch name, the commit messages, the PR title. Say where.

```
arcus issue show <key> --json > W/issue.json
```

No key anywhere: go on without a story, and the comment says none was linked. Never pick a story yourself.

The check reports on a PR. `gh pr view --json number,url,isDraft`. None: show the developer
`gh pr create --draft --fill` and run it after their yes. A PR that is not a draft: say it is already in review.

## 3. Regression lane, on the change

```
node S story-tests --issue W/issue.json
node S run --url <pr url> [--var ...] <files> > W/regression-pr.json
node S run --url <pr url> [--var ...] <failed files> > W/regression-retry.json
```

It lists only files this checkout has; a case whose file is elsewhere is not run. None listed: the comment
says "no automated tests for this story yet". When `ARCUS_PR_CHECK_RESET` is set, run it before
every run of the story tests. Never fix, edit or weaken a story test here.

## 4. Break lane

Decide whether it runs, as the reference says, and say why. Then start the `pr-check-breaker` subagent. Start it in the
background and tell the developer: the check is running on the working tree, so they must not change the code
until it says it is done. Its prompt holds only: the issue key, `W`, the merge base (`git merge-base origin/<base branch>
HEAD`), the PR address, the story test files, the budget, `ARCUS_STACK_DIRS`, `S`, and the paths
`${CLAUDE_PLUGIN_ROOT}/skills/author/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/skills/run/SKILL.md`, so it writes by
`/arcus:author`'s rules and runs by `/arcus:run`'s. Never your own view of the change. When it is done it has written `W/break-candidates.json`, `W/break-pr.json`, `W/break-retry.json` and
`W/stats.json`.

## 5. The base build

Run `ARCUS_PR_CHECK_SWITCH` and wait until the address answers. Then, after `ARCUS_PR_CHECK_RESET` if set:

```
node S run --url <base url> [--var ...] <story test files> > W/regression-base.json
node S run --url <base url> [--var ...] <candidate files> > W/break-base.json
```

Run `ARCUS_PR_CHECK_RESTORE` right after, even when a run failed, and check the address answers again.

## 6. Judge

```
node S diff --lane regression --pr W/regression-pr.json --base W/regression-base.json --retry W/regression-retry.json --issue W/issue.json > W/regression.json
node S diff --lane break --pr W/break-pr.json --base W/break-base.json --retry W/break-retry.json > W/break.json
node S packets --issue W/issue.json --out W/judge --diff W/regression.json --diff W/break.json > W/packets.json
```

For each entry of `W/packets.json`, start `pr-check-judge` with only: `Judge the difference in <packet path>.` Run them in
parallel. Write their answers, in packet order, as a JSON array to `W/verdicts.json`; an answer that is not one JSON
object goes in as it is and counts as unclear. Never change, drop or argue with a verdict.

## 7. Fix or ship

Show every finding the judge called `real_bug` or `ambiguous`: the title, the verdict and reason, and where its
screenshots are. For each, ask the developer: fix it, or ship it with a one-line reason.

- **Fix**: the developer or their agent changes the app's code. Re-run that test on the change; it passes: `fixed`. It
  still fails: ask again. Never change the test to make it pass.
- **Ship**: record their reason as they wrote it. A story case shipped unfixed still blocks, and CI's re-run will fail.

Write `W/decisions.json`: `[{"n": <packet number>, "choice": "fixed"}, {"n": ..., "choice": "shipped", "reason": "..."}]`.

## 8. Report and comment

```
node S report --issue W/issue.json --pr-url <url> --base-url <url> --diff W/regression.json --diff W/break.json --verdicts W/verdicts.json [--decisions W/decisions.json] --stats W/stats.json [--local] --comment W/comment.md > W/report.json
```

Pass `--local`. Find the PR's comments that start with `<!-- arcus:ran-locally -->` (a "Ran locally" comment) or
`<!-- arcus-pr-check:v1 -->`, save the body of one to `W/current.md`, and build the new body:

```
gh api repos/<owner/name>/issues/<n>/comments --paginate --jq '.[] | select(.body | startswith("<!-- arcus:ran-locally -->") or startswith("<!-- arcus-pr-check:v1 -->")) | {id, body}'
node S splice --section W/comment.md --into W/current.md > W/body.json
```

Write `body` from `W/body.json` to `W/body.md`, then edit that comment (`gh api -X PATCH
repos/<owner/name>/issues/comments/<id> -F body=@W/body.md`), or add one (`gh pr comment <n> -R <owner/name> --body-file
W/body.md`). Show it and post after a yes; a later run edits it with no new yes. No PR or no `gh`: print it.

## 9. Findings become pending tests

Every break-lane finding judged `real_bug`, fixed or shipped, is a test worth keeping. Hand those files to `/arcus:push`
as new cases (`arcus test push <files> --new`, after step 2's `arcus issue show`): they land in QI as pending cases on the
story. `ARCUS_PR_CHECK_PUSH=1` is the yes `/arcus:push` asks for; still show its dry run first. Without it, ask. Never
pass `--accept`, and never run `arcus test accept`.

Then delete every `pr-check-*.sigma` file and any element this run created that was not pushed. Never commit them.

## 10. Say

The story, the regression result, the scenarios run and found, each decision, the conclusion, the comment's link, what
was pushed, and what did not run and why. If no story case still blocks, offer `gh pr ready <n>` and run it
only after a yes.

## What this skill never does

- Edit a story test or a case's expected result, or weaken a scenario.
- Write scenarios itself, or give the breaker or the judge more than this skill says. Change or drop a verdict.
- Record a choice the developer did not make, or call a finding fixed before its test passes on the change.
- Switch the base without a clean tree, or leave the base build serving.
- Run a build the user did not name, or guess an address.
- Create a PR, post, push or mark ready without a yes.
- Accept anything, sign in, or start the agent or the app.
- Commit scenario files, or leave them in `tests/`.
