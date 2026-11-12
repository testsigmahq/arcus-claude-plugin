---
name: setup
description: Use when a developer wants to start using Arcus in a repo, or when authoring, running or pushing fails because something may be missing. Checks the arcus CLI, the sign-in, the project, its mode (direct or qi), its platforms, and whether this machine can run web and Android tests. Reports what is ready and stops with the one next step. Changes only local files, and only after the user agrees. Not for switching the mode of a working project (use mode).
---

# Setup: is this repo ready for Arcus?

Read `${CLAUDE_PLUGIN_ROOT}/references/workflow.md` first if you do not know the two modes. Check in this order, cheapest
first. Stop at the first thing that is not true.

You never sign the user in and you never handle credentials. Setup reads from Arcus and QI. It writes only to the repo
and to the CLI settings, and only after the user says yes.

## 1. The CLI

Run `arcus --version`.

- Not found: stop. Say the CLI is not installed. Give one command: `npm i -g @testsigma/arcus-cli` (Node 22 or newer).
  Do not install it for the user.
- Found: run `arcus docs --topic project-layout --json`. It needs no project. The output must be JSON with `id` and
  `markdown`. If not, the CLI is too old or is another program: stop and give the same command.
- Then run `arcus context --help`. If it fails, this CLI has no QI commands. Say that direct mode still works and that
  qi mode needs a newer CLI. Give the same command.

## 2. The sign-in

Run `arcus auth status --json`. If `loggedIn` is `false`, stop. The user signs in, in a terminal:

```
arcus auth login --region us     # us, in or eu
```

Ask which region the account is in. Never guess it from the locale or the email. Wait, then check again. Exit `2` from
any later command also sends the user back here. Note: `arcus run`, `check`, `fmt` and `docs` need no sign-in.

## 3. The project and its mode

Find `arcus.json` here or above.

### No `arcus.json`

1. Run `arcus project list`. Show the projects. The user picks one. Do not pick for them.
2. Ask where tests go, only for the first project: the default `tests/arcus`, or `.` for a repo that holds only Arcus
   tests.
3. Ask the platforms: `web`, `android`, `ios`, or a mix. Default `web`. More platforms make `arcus check` stricter.
4. Ask the mode, in plain words. **direct**: a push puts tests in Arcus at once. **qi**: a push sends tests to QI as
   versions that a reviewer accepts. Without `--mode`, the CLI picks `qi` when the account uses QI case versions, and
   stops when it cannot tell. Do not choose for the user.
5. Say what `init` does (it writes `arcus.json`, makes `<folder>/<project>/tests/` and `elements/`, adds `.arcus/` to
   `.gitignore`). After a yes, run:

   ```
   arcus init --project <id> [--dir <folder>] --mode <direct|qi> [--platforms <list>]
   ```

### There is an `arcus.json`

- Run `arcus project mode`. It prints the mode, and says when `arcus.json` names none (then it is `direct`). A line
  that says the lock and the mode disagree means: stop and use `/arcus:mode`.
- Region: each project has a `region`. It must equal the signed-in region, or a push stops with exit `2`.
- Several projects: ask which one, and pass `--project <name>` to later commands.
- Platforms: `arcus project platforms`. To change, after a yes: `arcus project platforms add <platform>` or `remove`.

## 4. Look at the repo

- `arcus.lock` must be committed. If `git check-ignore arcus.lock` prints it, tell the user to remove it from
  `.gitignore`.
- Fresh clone in qi mode (a lock, no `.arcus/`): tell the user to run `arcus pull --rebuild` once (`/arcus:sync`).
- Fresh clone in direct mode: the first push adopts files equal to Arcus and refuses files that differ.

## 5. Can this machine run tests?

This step never stops setup. It matters only for `/arcus:run` and `/arcus:verify`.

- Web (the project lists `web`): `arcus browsers list`. It lists browsers: ready. A message that starts `Cannot reach`
  means the local agent is not running. The user must start it. You cannot.
- Android (the project lists `android`): run `arcus devices list`. Ready means state `device`. `unauthorized` and
  `offline` need the user: unlock the phone and accept the USB prompt, or reconnect it or restart the emulator. No
  device: connect one or start an emulator. Several ready devices are fine: a run then needs `--device <serial>`.
  - If it says the Android tools (adb) were not found, the tools folder is not set. It is the Testsigma agent install
    folder (it has adb and Appium), or a plain Android SDK folder (then `appium` must be on PATH). Ways to set it, in
    the order the CLI reads them: the `ARCUS_ANDROID_TOOLS_DIR` variable in the shell, a `.env` file, then
    `arcus config set android.toolsDir <folder>`. Prefer the variable or `arcus config set`. With a yes, run the
    `config set` command. A `.env` value must be an absolute path (or start with `~`) outside the repository, or the CLI
    refuses it (exit `3`). Do not write a `.env` file for the user without a yes, and never read one. Check with
    `arcus config show`. With none of them set, the CLI tries `ANDROID_HOME`, `ANDROID_SDK_ROOT`, the usual SDK folder
    and `adb` on PATH, so a normal SDK install needs no setting.
  - The CLI starts and stops Appium itself. Do not start it. A start takes 10 to 25 seconds. Only a user who already
    runs an Appium sets `ARCUS_ANDROID_APPIUM_URL`, in the shell.
  - The app under test: `--app` on a run, or the `android` block of `arcus.json`: `app` (only a relative path to an
    `.apk` inside the project folder), `appPackage`, `appActivity`, `device`, `capabilities`. All are optional. No
    secret goes in it. With a yes you may edit that block only, then run `arcus project platforms` to see that the
    file still parses. The details are in `${CLAUDE_PLUGIN_ROOT}/references/running.md`.
- `ios` runs are not supported.
- If `arcus run --help` has no `--platform`, the CLI has no Android runs yet. Say so.
- A physical phone and Windows have not been tested yet. Say so if the user asks.

## 6. Report

```
Ready.
  arcus CLI    installed (<version>)
  signed in    <email>, region <region>
  project      <name>, mode <direct|qi>, platforms <list>, tests in <folder>
  can run      web: <browsers> | android: <device or "no device">
Next: /arcus:context <KEY> (qi), /arcus:author, /arcus:run or /arcus:push
```

When a line is not true, name it, give the one thing to do, and stop.

## What setup does not do

- Write tests, run them, push them, accept, or switch a working project's mode.
- Run `arcus auth login`, `arcus push` or anything that changes Arcus or QI.
- Edit `arcus.json` beyond the `android` block, or touch `arcus.lock` or `.arcus/`.
