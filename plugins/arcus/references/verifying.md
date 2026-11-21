# Verifying an issue: the command and the gap report

Details behind `/arcus:prove`. The skill says the order. This says the command and the shapes.

## `arcus issue verify`

It reads the issue from QI, then runs each case on this machine's build. It runs the local file when QI holds the same text. Otherwise it runs QI's script. It writes nothing to QI, to Arcus or to the repo. In a direct project it stops with exit `3`: say it is a QI command (`/arcus:mode`). It needs the sign-in (exit `2`: `/arcus:setup`).

### Before you run

- Ask for the issue key if the user gave none.
- Same checks as `/arcus:run`: the platform, a ready browser or device, the address (`--base-url`), the `{env.<name>}` values (`--var`). Secrets go as `--var name="$VARIABLE"` set by the user. Never type one, never read `.env` files.
- On Android, the options are the same as for a run: `--platform android`, `--device <serial>` (needed when several devices are ready), and `--app`. The setup, the app rules and the troubleshooting are in `${CLAUDE_PLUGIN_ROOT}/references/running.md`.
- Tell the user the address and the platform (on Android, the device too). Many cases run one after another and may take long. Run only when the user asked, or said yes to your offer.

### Run

```
arcus issue verify <KEY> --json --project <name> [--platform <web|android>] [--base-url <url>] [--var <name>=<value>]
    [--headed] [--browser <name>] [--device <serial>] [--app <path-or-url>] [--timeout <seconds>]
```

Give the Bash tool a time limit longer than cases times the timeout. On Android, `arcus issue verify` starts Appium once for the whole command (10 to 25 seconds), and the output has the lines `platform:`, `device:` and `tools:`. Say them. A `failing` case on Android may only say `Step failed`: look at `results.ndjson` and the screenshot of that case's run folder (`.arcus/runs/`) before you judge it, as `/arcus:run` says.

### Read the answer

Read `cases[]` and each `verdict`, not only the exit code. Exit `1` means some case is not `covered` or `rejected`.

| Verdict of the CLI | Means, and what to do |
|---|---|
| `covered` | Passed. Say whether the file or QI's script ran (`ran`) |
| `failing` | Failed, or could not run (`reason`). Go to `/arcus:run` for that file: look, name the owner, fix the test only if it is the test's fault |
| `missing` | No script in QI and no file. `/arcus:author` writes it. `arcus case show <id>` has the steps |
| `local_only` | The file ran, but QI holds no script. Push it (`/arcus:push`) |
| `rejected` | A reviewer rejected it. Listed, not run. Not counted against the build |

`local_differs: true` means QI's script ran because the file is not the text QI holds. Tell the user: pull (`/arcus:sync`) or push so the two agree. `next` in the answer says what to do for the whole issue. A verify run is not the run that a push needs: only `arcus test run` saves that.

### Session and a closed session

The issue is read in one session (a sprint or an ad hoc session). If the issue is in several sessions, the developer chooses one with `arcus issue show <KEY> --session <id or human id>` (see `/arcus:align`). Never choose for them. In an ad hoc session each case has `issueMatch` (`this_issue`, `other_issue`, `unknown`). Report `this_issue` and `unknown` cases as the expectation, and name the `other_issue` cases apart. If the session is closed (`sessionClosed`), verify still runs and reports. QI takes no new versions there, so there is nothing to push.

With case versions off, a case has no version to read a script from. Only the local file runs. A case with no local file cannot run.

## The gap report

One verdict for each case of the issue, not only the cases the change touched. The verdicts are the five above and one more, **not verified**: a case this machine cannot run (no browser, no device, no build, a missing secret). The CLI shows it as `failing` with a `reason`. Give the reason and let the developer decide.

| Verdict | In the report |
|---|---|
| covered | Passed on this machine |
| failing | The step that failed, and your judgment of the cause: the code, the test or the setup |
| missing | No test yet. Say why, if you did not write one |
| local only | A test with no case in QI. It can be pushed as a new case |
| rejected | Listed, not run |
| not verified | The reason. The developer decides |

Then a list of **additions**: behaviour that you built and that no case and no acceptance criterion asks for. The code difference is only for this list. It does not choose which cases to report.

How you keep the report is your choice. No file is required.

### Intent changes

A test that fails because the app now does, on purpose, what a case says it should not, is not fixed in the test. The change may be right. The case owner decides in QI. List each one in the report:

| Case | Review | Step | The case expects | The app now does | Why the change looks intended |
|---|---|---|---|---|---|

"Why" cites the diff or the story: a line, a commit message, the acceptance criteria. If nothing says it was intended, it is not an intent change. It is a finding: the code is wrong.
