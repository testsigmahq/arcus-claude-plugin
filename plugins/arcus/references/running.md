# Running a test: the result, the messages, and who owns a failure

`arcus run <file> --json` prints one JSON object on stdout. Read it. Do not guess from the exit code.

## The shape

```
{ sigmaLang, converter, runner, browser: {name, version} | null, platforms: [...], platform: "web"|"android",
  device: {serial, model, kind} | null, tools: {layout, source, path} | null,
  run: { path, title, status, durationMs, totalSteps, passedSteps, failedSteps, skippedSteps,
         failedStep?: {description, message, screenshot?}, problem?, interruptedAt?,
         diagnostics: [...], artifactsDir: <folder> | null } }
```

- `status` is `passed`, `failed`, `refused` or `interrupted`.
- `failedStep.description` is the step as written in the file. `message` is plain text. `screenshot` is the absolute path
  of a `.jpg` of the page at that step. Open it with the Read tool.
- `problem` is set when there is no failed step to show: the run was stopped, the browser went away, the test has no
  steps, or the run failed with no step error. `interruptedAt` is the step the run was on when it stopped.
- A run that hit the time limit is `failed`, with the step it was on and the message `timed out after N s`.
- `diagnostics` holds what `arcus check` found: the errors of a refused run, or the warnings of a run that went on.
- `artifactsDir` is the run's own folder, under `.arcus/runs/`. It holds `runner-output.log`, with the engine's own
  output, and on Android `results.ndjson`, with one line for each step. Read the log only for a `problem` that nothing
  else explains. `browser` and `artifactsDir` are `null` when the test was refused before a browser was chosen. On an
  Android run `browser` is always `null`, and `device` and `tools` say where the run went.
- Counts cover the steps that ran. After a failure the later steps are `skippedSteps`.

## Exit codes

| Exit | Means |
|---|---|
| `0` | passed |
| `1` | the test failed, was refused, or was interrupted: read `run.status` |
| `3` | this machine cannot run it, or an option is wrong (no Android tools, no device, a device that is not authorized or is offline, several ready devices, Appium did not start, a wrong flag). stdout is empty; stderr is JSON with `message`, `code`, `remediation` |

It is never `2`: a run does not talk to Arcus.

## Setup errors (exit 3)

| Message starts with | Owner | Say |
|---|---|---|
| `Cannot reach the …agent` (the CLI's own text) | the user | Start the local agent. If it runs somewhere else, `arcus config set execution.localUrl <url>` |
| `… has no web platform` or `… has no android platform` | the user | Pick a platform the project lists with `--platform`, or ask before `arcus project platforms add <platform>` |
| `ios runs are not supported yet` | the user | Say it as it is |
| `The Android tools (adb) were not found` or `… is <folder>, but adb is not in it` | the user | Set the tools folder. See "Android: tools, device, app" below |
| `ARCUS_ANDROID_TOOLS_DIR in <file> is …, which is not an absolute path` (or `is inside the repository`, `holds the repository`) | the user | A `.env` file may name only an absolute folder outside the repository. Use the shell variable or `arcus config set android.toolsDir <folder>` |
| `Appium was not found` | the user | The tools folder has no Appium. Update the agent folder, or install Appium and put `appium` on PATH |
| `Appium stopped while starting`, `Appium was not ready after N s`, `Appium could not bind a port` | the user | Read the Appium log. The message gives its path (`.arcus/runs/appium-<time>-<pid>.log`) |
| `The Appium server at … is not ready` | the user | `ARCUS_ANDROID_APPIUM_URL` is set in the shell and that server does not answer. Start it, or unset the variable so arcus starts its own |
| `No Android device is connected` | the user | Connect a device with USB debugging on, or start an emulator. Check `arcus devices list` |
| `More than one device is ready` | the user | Ask which one. Pass `--device <serial>`, or set `device` in the `android` block |
| `Device <serial> … is not authorized` | the user | Unlock the device and accept the USB debugging prompt |
| `Device <serial> … is offline` | the user | Plug the cable in again, or restart the emulator |
| `Device <serial> (--device) is not connected` | the user | The serial is wrong. The message lists the connected ones |
| `The app file … does not exist` | the user | Fix `--app` or the `app` of the `android` block |
| `The app … (android.app in arcus.json) is a URL` (or `is an absolute path`, `leads out of the project folder`) | the user | In `arcus.json` the app is only a relative path inside the project folder. Pass anything else with `--app` |
| `The capability "…" in the android block of arcus.json is not allowed` | the user | The message lists the allowed capabilities. Remove the name, or use a field of the block (`app`, `appPackage`, `appActivity`, `device`) |
| `--browser is a web option, and this run is on android` (or `--device is an android option, and this run is on web`) | you | A flag of the other platform. Remove it, or pass the right `--platform` |
| `ARCUS_ANDROID_APPIUM_URL … has a user name or password` (or `is not a valid URL`) | the user | Give the address without credentials, or unset it |
| `Browser '…' is not available` | the user | Pick one from `arcus browsers list` |
| `The browser could not start` | the user | The binary the agent named cannot start. Name it. The log path is in the message |
| `--timeout …`, `--var …`, `--screenshots …`, `base_url is given twice` | you | You passed a wrong option. Fix it and run again |
| `no path was given`, `N paths were given`, `… is a folder`, `… is a pattern`, `… is not a test of project …`, `No such file or directory` | you | A run takes exactly one test file of the project. Name one |
| `The runner compiles sigma-lang …; this arcus runs …`, `The runner and this arcus … use different sigma-lang versions` | the user | The CLI and its runner do not match. The message says what to install. Usually `npm i -g @testsigma/arcus-cli` |

## Android: tools, device, app

Android runs need three things: the tools (adb and Appium), a ready device, and an app. `arcus devices list` shows the
devices. `arcus devices list --json` gives the same as data. The state `device` is ready. `unauthorized` and `offline`
need the user. The CLI starts Appium by itself, uses it for the run, and stops it. You never start Appium. A cold start
takes about 10 to 25 seconds, so give the Bash tool a long time limit. Appium writes a log to
`.arcus/runs/appium-<time>-<pid>.log`. A start error names that path. Each run prints a `device:` line and a `tools:`
line (the folder and where it came from). Show them to the user.

**The tools folder.** The CLI looks in this order and takes the first that is set:

1. `ARCUS_ANDROID_TOOLS_DIR` in the shell environment.
2. The same key in a `.env` file at the repository root, or in the current folder.
3. `arcus config set android.toolsDir <folder>`. The CLI stores an absolute path.
4. `ANDROID_HOME`, then `ANDROID_SDK_ROOT`, then the usual SDK folder of the system, then `adb` on PATH.

The folder can be the Testsigma agent install folder (it has adb and Appium), or a plain Android SDK folder. With an SDK
folder, `appium` must be on PATH. A folder that was named on purpose and has no adb is an error.

**A `.env` file is limited, on purpose.** A cloned repository must not choose the programs that run. So a `.env` value
must be an absolute path (or start with `~`) outside the repository and the current folder. Anything else exits `3`.
The CLI reads only keys that start with `ARCUS_ANDROID_` from it. Do not write or change a `.env` file for the user
unless they say yes. Prefer the shell variable or `arcus config set`. Never read `.env` files to find a value.

**An Appium that already runs.** `ARCUS_ANDROID_APPIUM_URL` makes the run use that server and start none. The CLI reads
it from the shell environment only, never from `.env`, and `arcus devices list` ignores it. A URL with a user name or
password is refused. Only the user sets it.

**The device.** `--device <serial>`, else `android.device` in `arcus.json`, else the only ready device. With several
ready and none named, the CLI exits `3` and lists them: ask the user which one.

**The app.** `--app <relative path | absolute path | URL>` on the command line. In `arcus.json` the optional `android`
block has:

| Field | Holds |
|---|---|
| `app` | Only a relative path to an `.apk` inside the project folder. A URL or an absolute path there exits `3`: use `--app` |
| `appPackage`, `appActivity` | What to open. `launch app` uses them |
| `device` | A serial |
| `capabilities` | Session-tuning capabilities from a closed list (for example `noReset`, `autoGrantPermissions`, `newCommandTimeout`, `appWaitActivity`). Any other name exits `3`, and the message lists the allowed ones |

With no app information, the session starts on the device as it is, and `launch app` fails at run time. Give `--app`,
set `android.appPackage`, or write `launch app "<package>"`. An app that is not installed fails with
`Cannot start the '<package>' application` and no step result. No secret goes in `arcus.json`.

## Failure messages, and who usually owns them

The message tells you where to look. It does not decide the owner. The screenshot and the app decide.

| Message | Usually | Look at |
|---|---|---|
| `No element on the page matched this step's locator within 5s` | the test (a wrong locator) or the app (the control is gone) or timing (the page was still loading) | The screenshot: is the control on the page? Is it there under another label, or inside a frame? Is the page the one the test meant? |
| `Expected "…", but the actual …` and other verify mismatches (they name the element and the actual value) | the test (the wrong expected text) or the app (a wrong text) | The app source for that string. If the app and the test disagree about what is right, ask the user |
| `This URL could not be reached`, `The domain name could not be resolved` | the setup | The address in the `nav`. Is the app running? Is the address right, with the port? Do not change the test to another address without the user |
| `The certificate for … was rejected` | the setup | A self-signed staging certificate. Tell the user. Do not turn checks off |
| `Unresolved reference: "<name>" not found in environment` (in the log, or in the step message) | the setup | A `{env.<name>}` has no value. Pass `--var <name>=…`, or `--base-url` for `base_url` |
| `timed out after N s` | the app is slow, or a wait step is longer than the limit, or the run hung | The step it was on. A long `wait` is the test's. Do not raise `--timeout` just to pass |
| `The test has no steps to run` | the test | An empty test |
| `The run failed but no step reported an error`, `The runner returned no results` | the CLI or the runner | Show the message and the log path. Do not loop |

## Android troubleshooting

Read these before you judge the test.

| Symptom | Cause | Next step |
|---|---|---|
| The failed step says only `Step failed` | The engine hides the real cause in the message | Open `results.ndjson` in the run folder (`run.artifactsDir`, under `.arcus/runs/<runId>/`) and the failure screenshot. The real cause is there (for example, element not found). Read both before you say who owns it |
| The first run after `--app` fails once with `The instrumentation process cannot be initialized` | The app was just installed and the device was not ready | Run again. Judge only the second run |
| `Cannot start the '<package>' application`, no step result | The app is not installed, or the package name is wrong | Check the package. Pass `--app`, or set `android.appPackage` |
| `launch app` fails and no app was given | The session started on the device as it is | Use `--app`, `android.appPackage`, or `launch app "<package>"` |
| Element not found on a Jetpack Compose app | Compose often has no ids and no content descriptions | Find buttons by their visible text. Find text fields by position, for example `locate xpath "(//android.widget.EditText)[1]"` |
| Element not found with `locate text "<part>"` | `locate text` matches the whole text only | Write the full text, or use xpath `contains(@text,'…')` or uiautomator `textContains` |
| `arcus check` or `arcus run` refuses a step | The step is web only on Android (see `${CLAUDE_PLUGIN_ROOT}/references/platforms.md`) | Change the step to a form that Android has |
| Exit `3`, no tools, no device, `unauthorized`, `offline`, several devices | Setup | The table above, then `/arcus:setup` |
| Appium does not start | The Appium log has the reason | Read the log named in the message. Tell the user. Do not loop |
| A step on a device action, an alert, a web view, an install or an image fails | These were not tested on a device yet | Say so. Do not promise it works. Show the screenshot and the step |

A physical phone and Windows have not been tested yet. Say so if the user asks.

A failure that is the app's belongs to the user. Report it with the screenshot and the step. A test that rightly fails
because of a bug in the app is a good test. Do not change it.

## Reading the screenshot

The Read tool shows a `.jpg`. Look for: the page you expected (a login page when you expected the home page is a
navigation or sign-in problem, not a locator one), an error banner or a cookie wall that covers the control, the control
under a different label, a spinner that has not finished. Say what you see in a sentence.

## Options

| Option | Use |
|---|---|
| `--headed` | Show the browser. Only when asked, or to debug. Default is hidden |
| `--browser <name>` | A browser from `arcus browsers list`. Default: Chrome for Testing, then Chrome |
| `--screenshots all\|failed\|none` | Default `failed` |
| `--base-url <url>` | Sets `{env.base_url}`. A test must use it as `nav "{env.base_url}/path"`: there is no relative `nav` |
| `--var <name>=<value>` | Sets `{env.<name>}`. Repeat for more. A secret is passed as `"$VARIABLE"`, never typed |
| `--timeout <seconds>` | Default 300. Counts from the start of the browser |
| `--platform <web\|android>` | Default: the project's only platform; `web` when it has several and one is web; with several and no web, the flag is needed. `ios` is refused. A web flag (`--browser`, `--headed`) on an Android run, or an Android flag (`--device`, `--app`) on a web run, exits `3` |
| `--device <serial>` | Android: a serial from `arcus devices list`. Default: `android.device` in `arcus.json`, else the only ready device |
| `--app <path or URL>` | Android: an `.apk` (a relative path from the current folder, an absolute path, or a URL) to install and test. No secret in the URL |
| `--note "<why>"` | Why the run ended as it did. Kept with the run and sent with the next push to QI. Facts only, no secrets |
| `--project <name>` | The project's folder name, or its id. Needed at a repo root with several projects |

## What the run leaves behind

`.arcus/runs/<id>/`, in the repo. It is local state, and git ignores it. A run never changes the test files,
`arcus.lock` or `.arcus/base/`.

## A run is evidence for a push

A run that ends `passed` or `failed` is saved in `.arcus/` with the hash of the file, the platform, the device and the
note. There is one local record for each test path and platform (`.arcus/evidence/<path>.android.json`,
`<path>.web.json`), so an Android run does not replace the web run of the same test. In qi mode, when the policy says
`run: required`, `arcus push` accepts a file only if it has a run of the file as it is now. The gate takes the newest
matching record of any platform, and the push plan shows the platform and device of the run it uses. Any edit makes the
run old. A failed run counts as a run: QI shows it as failed, not executed. `interrupted` and `refused` runs are not
saved. `arcus verify` saves nothing.

When the policy says `run: optional`, a push with no run is allowed. The dry run, the result and `arcus status` then
show `no local run`. Say it as it is: it is not a pass.
