---
name: prove
description: Use when a developer or their coding agent has changed a user-facing flow on a QI issue and wants to prove the change works before review ("prove CW-412", "prove this change", "get this PR ready with tests"). Runs the whole loop over the other skills - reads the issue's cases, writes the missing tests, runs them on this machine until they pass, writes one "Ran locally" comment for the PR, and pushes the tests to QI as pending. Accepting waits for the PR to merge, and the developer does it. Qi mode only. Never edits what a case expects, never weakens a test, never accepts.
---

# Prove: the developer loop for one issue

QI's cases say what must work. You automate those, run them against the app on this machine, show the result on the PR,
and push the tests for review. You do not decide from the diff what to check: the cases do. The diff only tells you which
cases this change touches.

This skill only orders the others. Each step follows that skill's rules and gates: `/arcus:context` reads the issue,
`/arcus:author` writes, `/arcus:run` runs, `/arcus:verify` checks the issue, `/arcus:push` sends, `/arcus:accept`
accepts. Read each one when you reach its step. In a direct project, stop: say prove is a QI flow (`/arcus:mode`).
Not signed in (exit `2`): `/arcus:setup`.

The comment's shape, the marker and the intent-change table are in `${CLAUDE_PLUGIN_ROOT}/references/proving.md`.

## 1. The issue and its cases

Follow `/arcus:context`: the issue key from the user (or the branch, offered and confirmed), then `arcus issue show <KEY>
--json`. Read the diff (`git diff <base>...HEAD`) and say which cases the change touches, and why, in a few words. A case
it does not touch is left alone: name it as not touched.

- **No cases.** Stop. QI makes the cases from the acceptance criteria: tell the user to generate them in QI for this
  issue, then run `/arcus:prove` again. Do not invent cases to fill the gap.
- **A changed flow no case covers.** One new test for it, pushed later with `--new`, marked **new** in the comment.
  Never more than the change needs.
- **Sprint closed**, **policy** `run: required`, a stale context: say them now, as `/arcus:context` says.

## 2. Tests for the touched cases

For each touched case with no file, or in `REWORK`, or with a `suggestion`: read its steps with `arcus case show <id>
--json`, and write or change the test through `/arcus:author`. The test covers every step of the case, in its order;
each expected result is a `verify`. A step the language cannot express is a gap: say it in the comment, do not drop it.

## 3. Run until green

Each test through `/arcus:run`'s rules, on the address and platform the user has seen. When a test fails, find the owner
first, with the screenshot, as `/arcus:run` says. Then:

| Owner | Do |
|---|---|
| The code of this change | Fix the code. Run again. This is the point of the loop |
| The test: a locator, a wait, the setup of the test | Fix the test with `/arcus:author`'s rules. Run again |
| The case: the app now does on purpose what the case says it should not | **Do not edit the step or the `verify`.** It is an intent change. Leave the test failing and list it (step 5) |
| The setup | Say what to fix and stop |
| The evidence does not decide | Show it and ask |

A change is on purpose only when the diff, a commit message or the story says so. Otherwise the code is wrong: fix it.
The limits of `/arcus:run` hold: three rounds per test, stop at once on the same failure twice.

**Never weaken a test to make it pass.** No deleted `verify`, no expected value changed to what the app showed, no wait
added to hide a fault, even if the user says the app is right: for a case, that is the case owner's call in QI. Any edit
to a test's steps or `verify` lines after its first run is listed in the comment.

## 4. Check the issue

When the touched tests pass, run the issue once through `/arcus:verify`:

```
arcus issue verify <KEY> --json --project <name> [--base-url <url>] [--var <name>=<value>]
```

Read every case's verdict, as `/arcus:verify` says, and build the comment's table from them. `covered` means passed on
this machine: the developer's signal, not the PR's check and not an Arcus run. `ran` says whether your file or QI's
script ran: when QI's script ran and it differs from your file (`local_differs`), say so, and do not push your file over
it before you know which one the case means.

## 5. The comment

Write one "Ran locally" comment, in the shape `references/proving.md` gives, every time you ran anything, including
when a setup or data problem stopped the run early: the comment is how the reviewer learns what was not proven. It says:

- that this is the developer's own run on their machine, with the commit and whether it had uncommitted changes,
- each case: touched or not, automated or new, its verdict, and for a failure the step and the screenshot path,
- proposed intent changes: the case, the step, what the case expects, what the app now does, and why it looks intended,
- what did not run, and why,
- any change to a test's steps or `verify` lines after its first run.

Posting it shows it to the team. Show the comment, and post it only after a yes, once per PR. Later runs edit the same
comment, found by its marker, and need no new yes. With no PR, print it for the user to paste.

## 6. Push, pending

Hand over to `/arcus:push` for the tests from step 2: `--case <id>` for a case's file, `--new` for a new test. Its dry
run and its yes apply. Each test lands as a pending head on its case. **Never pass `--accept`.** Say that elements go
straight to Arcus, unreviewed, when the plan lists any.

## 7. After the PR merges

Accept is not part of this run. When the user says the PR merged, check it (`gh pr view --json state,mergedAt`). Then:

- the policy lists a developer (`policy.acceptBy`): give the developer the exact `arcus test accept <path>` command for
  each passing test, and let them run it. `/arcus:accept` explains the results. Never run it yourself.
- otherwise: a reviewer accepts in QI. Say so.

Then QA confirms the accepted version. Intent changes and failing tests are not accepted until QI decides them.

## Report

Say, briefly: the issue, the cases touched, automated and new, each verdict, the intent changes waiting, where the comment
is, and what was pushed. Then the next step: fix and `/arcus:prove` again; wait for QI on intent changes; or, after the
merge, accept.

## Never

- Choose what to test from the diff alone, or invent cases for an issue that has none.
- Edit a step or a `verify` of a case to match what the app now does.
- Weaken a test, or hide a gap or a test that did not run.
- Say a local run passed in Arcus or is the PR's check.
- Post the comment without a yes, or add a second one.
- Push with `--accept`, run `arcus test accept`, or accept before the PR merged.
- Start the agent or the app, sign in, or edit `arcus.json`, `arcus.lock` or `.arcus/`.
