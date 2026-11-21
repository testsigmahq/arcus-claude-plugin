---
name: align
description: Use when a developer starts work on an issue in a qi-mode project ("pick up CW-412", "start work on CW-412", "implement CW-412", "work on this issue", "what tests does this issue need"), or wants the manual steps of one QI case, or QI sent a case back for rework or a suggestion. Before the first code edit, reads what QI expects (the cases and their steps), shows a short expectation summary, and plans which tests to write or change. Writes no files. Not for direct-mode projects, and not for writing the test (use author).
---

# Align: read what the issue expects, before the code

In qi mode, QI holds the issue, the cases it made from the acceptance criteria, the review state of each case, and the policy. You ask QI first, so that nothing is built on an assumption. You do not invent what to test. The rules of the layer are in `${CLAUDE_PLUGIN_ROOT}/references/layer.md`. Who holds what is in `${CLAUDE_PLUGIN_ROOT}/references/workflow.md`.

If the project is in direct mode, `arcus issue show` and `arcus case show` stop with exit `3`. Say that align is a QI command, offer `/arcus:mode`, or go on with `/arcus:author`. If the CLI is missing or you are not signed in (exit `2`), run `/arcus:setup`.

## 1. Which issue

The user gives the issue key. If the branch name holds a key, offer it and ask. If the user starts work and names no issue, ask once. With no answer, go on and do not ask again. A wrong issue puts every push in the wrong place, so never guess it.

## 2. Read the issue

```
arcus issue show <KEY> --json
```

`arcus issue show` gives no manual steps. They come from `arcus case show <id>` (step 3).

Read: `issue`, `place` and `placeClosed`, `acceptanceCriteria`, `policy` (`acceptBy`, `run`, `contextMaxAgeHours`, `sprintClose`), `cases[]` and `related[]`, and `next`. Each case has `id`, `label`, `title`, `file` (null means no test file yet), `review`, `accepted`, `comments`, `suggestion` and, in an ad hoc session, `issueMatch`. The answer is saved in `.arcus/`. Never edit it.

Tell the user where QI holds the issue: the place. Give its type (`sprint` or `adhoc`), title, human id and status. A closed place still works here: say it is closed.

### Several places

An issue can be in several places. Then `place` is null and `places[]` lists them (`id`, `type`, `title`, `humanId`, `status`, `closed`, `caseCount`). Nothing is saved yet. Show the list and let the **developer** choose. Never choose a place for them, not even when one looks right. Then run the command again with the choice:

```
arcus issue show <KEY> --place <id or human id> --json
```

QI saves the choice with the issue context. Push, verify and status use it. Run it again with a new `--place` to change it.

### An ad hoc session

Each case has `issueMatch`: `this_issue`, `other_issue` or `unknown`. Say it per case. Count only the `this_issue` and `unknown` cases as what the issue expects. Name the `other_issue` cases, and say that they do not count. An ad hoc session may hold no tracker issue: `issue.id` and `issue.title` are then null.

Say in plain words, per case:

| What you see | Plan |
|---|---|
| `file` is null | A test to write. First push binds it with `--case <id>` |
| `review: REWORK` | Read the comments, change the file, run, push |
| `suggestion` | The story changed. Read the suggested steps, change the file, run, read the context again, push |
| `REJECTED` | Not yours to redo. Show the reason. See `/arcus:sync` |
| Accepted, no change | Nothing to do |
| `linked, primary story <KEY>` (`primary: false`, `primaryIssueKey`) | The case belongs to another story. It may already have a file and be accepted. Check `file` and `accepted` first. To push to it, read the context of its own story |

Also tell the user: the place is closed (QI takes no new versions: see below), the policy needs a run before a push (`run: required`), and the context goes stale after `contextMaxAgeHours` (a push refuses then: read it again). `related[]` are cases of linked issues. A fix that extends one goes on its line with `--case`. Their absence is not an error.

## 3. Read the steps of every case

```
arcus case show <id> --json
```

Do this for every case in `cases[]` before the first code edit. Read `related[]` too when QI has them. It gives `steps` (plain text), and `suggestion` with `steps` and `changes` when the story changed. Keep the steps so that they survive a compaction of the session. How you keep them is your choice. The CLI does not write the steps to disk: `arcus case show` is the way to read them again.

## 4. Show the expectation summary

Before the first code edit, always show a short summary in three parts:

- **Expects.** One or two lines for each case.
- **Unclear or in conflict.** What the cases, the acceptance criteria and the Jira text do not settle, or say differently. You decide if there is a conflict.
- **Missing.** What the issue needs that no case covers.

Then go on. Do not wait for a "yes". Stop only to discuss a conflict with the developer. The developer sorts a conflict out.

**No cases.** Do not stop. Go on from the Jira text and say that QI gives no expectation.

A useful habit, not a rule: write and run the test of a case when its flow is runnable, and do not leave all tests to the end. How and when you build is your choice.

## Refusals

| You see | Say and do |
|---|---|
| `issue_not_found` | QI has no place for the issue, or no such issue. Check the key and the project. QI gives no expectation: go on from the Jira text. For a new issue the user may push unmapped (`/arcus:push`) |
| `place_required` | The issue is in several places and none is chosen. Show the list. The developer chooses. Run `arcus issue show <KEY> --place <id or human id>` |
| `place_not_found` | QI has no such place for this issue. Show the places again (`arcus issue show <KEY>`) and let the developer choose |
| `place_closed`, `placeClosed` or `sprint_closed` | The place is closed. QI takes no new versions there. The developer may choose an open place, or use an issue of an open place that links to it |
| `versioning_changing` (exit `3`) | QI is changing how it stores case versions. Nothing changed. Try again later |
| `policy_forbids` | The Arcus role is too low. Ask a project admin |

## Hand over

Go on with the work on the issue. How you build the code is your choice. When you write the test of a case, use `/arcus:author`. When the work on the issue is done, use `/arcus:prove`. This skill writes no files and sends nothing.
