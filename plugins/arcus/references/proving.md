# Proving a change: the comment and intent changes

The details behind `/arcus:prove`. The skill says the order. This says the shapes.

## Intent changes

A test that fails because the app now does, on purpose, what a case says it should not, is not fixed in the test. The
change may be right. The case owner decides in QI. List each one:

| Case | Review | Step | The case expects | The app now does | Why the change looks intended |
|---|---|---|---|---|---|

"Why" cites the diff or the story: a line, a commit message, the acceptance criteria. If nothing says it was intended, it
is not an intent change. It is a finding: the code is wrong, so fix the code.

## The comment

The first line is the marker, so a later run finds the comment and edits it. Build the table from the verdicts of
`arcus issue verify --json` and the runs of the touched tests.

```markdown
<!-- arcus:ran-locally -->
### Ran locally: <issue key> <issue title>

The developer's own run, on their machine. Not an Arcus run and not this PR's check.
Commit `<short sha>` (uncommitted changes: yes|no) · <browser and version, or device> · <date and time>

| Case | Kind | Verdict | Steps | Time |
|---|---|---|---|---|
| TC-12 Sign in with SSO | touched, automated | covered | 6/6 | 14 s |
| Reset a forgotten password | new | failing at step 4: <message> | 3/7 | 9 s |

**Proposed intent changes** (waiting for QI)
<the intent-change table, or "None.">

**Not run**
<each case or test that did not run, and why, or "Nothing.">

**Tests changed after their first run**
<file: what changed and why, or "None.">

Pushed to QI as pending heads on <issue key>. Accepted after this PR merges.
```

Screenshots stay as paths on this machine (`.arcus/runs/…`). Do not attach them, and do not upload them anywhere. Write
the last line only after the push happened.

## Posting and editing

Find the PR: `gh pr view --json number,url`. Find an earlier comment by its marker:

```
gh api repos/{owner}/{repo}/issues/<number>/comments --jq '.[] | select(.body | startswith("<!-- arcus:ran-locally -->")) | .id'
```

- None, and the user said yes: `gh pr comment <number> --body-file <file>`.
- One: edit it, `gh api -X PATCH repos/{owner}/{repo}/issues/comments/<id> -F body=@<file>`.
- Write the body to a file under `.arcus/`, never into the command line.
- No PR, or `gh` is not signed in: print the comment and say where to paste it.
