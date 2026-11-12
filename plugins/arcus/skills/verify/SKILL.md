---
name: verify
description: Use when a developer wants to know if every case of a QI issue passes on this machine's build ("is CW-412 covered", "check the issue before I merge"). Runs each case of the issue locally, on web or Android, and reports covered, failing, missing, local only or rejected per case. Qi mode only. Writes nothing and sends nothing. Not for one test (use run) and not a substitute for the run a push needs.
---

# Verify: run every case of an issue

`arcus issue verify` reads the issue from QI, then runs each case on this machine's build. It runs the local file when QI
holds the same text. Otherwise it runs QI's script. It writes nothing to QI, to Arcus or to the repo. In a direct
project it stops with exit `3`: say verify is a QI command (`/arcus:mode`). It needs the sign-in (exit `2`:
`/arcus:setup`).

## 1. Before you run

- Ask for the issue key if the user gave none.
- Same checks as `/arcus:run`: the platform, a ready browser or device, the address (`--base-url`), the `{env.<name>}`
  values (`--var`). Secrets go as `--var name="$VARIABLE"` set by the user. Never type one, never read `.env` files.
- On Android, the options are the same as for a run: `--platform android`, `--device <serial>` (needed when several
  devices are ready), and `--app`. The setup, the app rules and the troubleshooting are in
  `${CLAUDE_PLUGIN_ROOT}/references/running.md`.
- Tell the user the address and the platform (on Android, the device too). They run many cases one after another and may take long. Run only when
  the user asked, or said yes to your offer.

## 2. Run

```
arcus issue verify <KEY> --json --project <name> [--platform <web|android>] [--base-url <url>] [--var <name>=<value>]
    [--headed] [--browser <name>] [--device <serial>] [--app <path-or-url>] [--timeout <seconds>]
```

Give the Bash tool a time limit longer than cases times the timeout. On Android, `arcus issue verify` starts Appium once for the
whole command (10 to 25 seconds), and the output has the lines `platform:`, `device:` and `tools:`. Say them. A `failing`
case on Android may only say `Step failed`: look at `results.ndjson` and the screenshot of that case's run folder
(`.arcus/runs/`) before you judge it, as `/arcus:run` says.

## 3. Read the answer

Read `cases[]` and each `verdict`, not only the exit code. Exit `1` means some case is not `covered` or `rejected`.

| Verdict | Say, and do |
|---|---|
| `covered` | Passed. Say whether the file or QI's script ran (`ran`) |
| `failing` | Failed, or could not run (`reason`). Go to `/arcus:run` for that file: look, name the owner, fix the test only if it is the test's fault |
| `missing` | No script in QI and no file. `/arcus:author` writes it. `/arcus:context` (`arcus case show <id>`) has the steps |
| `local_only` | The file ran, but QI holds no script. Push it (`/arcus:push`) |
| `rejected` | A reviewer rejected it. Listed, not run. Not counted against the build |

`local_differs: true` means QI's script ran because the file is not the text QI holds. Tell the user: pull
(`/arcus:sync`) or push so the two agree. `next` in the answer says what to do for the whole issue.

## 4. Report

One line per case with its verdict, then the build (`commit`, and whether there are uncommitted changes), then the
next step. A verify that shows `covered` for all is not an accept and not a push. Do not say the issue is done.

## Never

- Say a case passes when it was `local_only` or `missing`.
- Weaken a test to turn a `failing` into `covered`.
- Treat verify as the run that a push needs: only `arcus test run` saves that.
