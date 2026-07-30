---
name: testsigma-tests
description: Use when a developer asks to write, add, or generate end-to-end (e2e) tests for their application — authors the tests in Testsigma script (the code-v2 TypeScript DSL), places them under the repo's tests/ tree, validates them offline with the testsigma CLI, and offers to run them to verify.
---

# Authoring Testsigma script e2e tests

You write **end-to-end tests in Testsigma script** (the code-v2 TypeScript DSL)
and verify them with the `testsigma` CLI. Authoring is offline and safe; running
reaches a live target and is always gated behind explicit confirmation.

## Preflight — the CLI must be installed

Run `testsigma --version` (or `command -v testsigma`). If `testsigma` is not on
`PATH`, STOP and tell the developer to install/configure the testsigma CLI — do
not author from memory. The CLI is the source of truth for the DSL; authoring
without it risks drift.

## Step 1 — Detect the application type

Inspect the repo and pick the first confident match:

- **mobile** — `android/`, `ios/`, `*.xcodeproj`, `pubspec.yaml`, `react-native`
  in `package.json`, or Capacitor/Ionic.
- **web** — a web framework in `package.json` (React/Vue/Svelte/Next/Angular)
  without the mobile signals above.
- **api** — OpenAPI/Swagger files, or a backend framework
  (Express/Fastify/Spring/FastAPI/Rails) with no UI.

If signals conflict or none match, ASK the developer whether it's `web`, `mobile`,
or `api`. Never guess.

## Step 2 — Load the DSL reference from the CLI

Run, for the detected type `<t>`:

```bash
testsigma code reference --type <t>
testsigma code examples --type <t>
```

Read both. The reference is the authoritative DSL surface for the installed CLI;
the examples are working specs to pattern-match. Author strictly within what they
show — do not invent method names.

## Step 3 — Author the spec(s)

- Read the relevant application source for selectors / routes / endpoints.
- Choose the test directory: default `tests/testsigma/`. If the repo already has a
  tests convention (`e2e/`, `__tests__/`, `cypress/`, etc.), nest under it
  (e.g. `e2e/testsigma/`).
- Write `tests/<e2e-dir>/<feature>.spec.ts` — one spec per feature: `element()`
  declarations at the top, a focused `test(...)`, `expect(...)` assertions, and
  `reusable(...)` where steps repeat.

## Step 4 — Validate offline (always)

```bash
testsigma code validate --input tests/<e2e-dir>/<feature>.spec.ts
```

If it reports diagnostics, fix the spec and re-validate until clean. This needs no
running app, so always do it before offering to run.

## Step 5 — Offer to run (resolve the target first, then confirm)

`testsigma code run` reaches a **live target**. Fully resolve what it needs
BEFORE you call it, tell the developer exactly what you'll use, and run only on
an explicit "yes". **Never call `code run` with empty or placeholder caps** (a
mobile-only flag) — if you can't resolve the target, STOP and say what's missing
instead of running a call you know will fail.

- **web** — the target is **not a flag**: it is whatever the spec's `page.goto(...)`
  points at, so confirm that URL is reachable (offer to detect a local dev-server
  port, and edit the spec if it points elsewhere). Warn that a real browser window
  opens — the run is headed. Then:

  ```bash
  testsigma code run --input tests/<e2e-dir>/<feature>.spec.ts
  ```

  The browser comes from the agent, as devices do for mobile — `testsigma list
  browsers --local` shows them. Chrome for Testing is the default (agent-pinned, so
  a Chrome auto-update cannot shift a run). Two web-only flags, neither passed
  unless asked: `--browser <name>` (short names work: `chrome`, `edge`, `safari`,
  `firefox`, `cft`) and `--headless`. An unknown browser fails up front listing what
  the agent has — offer from that list rather than substituting. If a launch fails
  with "Executable doesn't exist", relay the CLI's remediation; never run
  `playwright install` unprompted.

- **api** — the API base URL and any required env (e.g. `API_PASSWORD`). Then run
  the same `testsigma code run --input tests/<e2e-dir>/<feature>.spec.ts`.

Every type needs the local agent running: the CLI reads its sigma converter path
from it. On "Could not reach the local agent", ask the developer to start it.

### mobile — a run needs a connected device AND the app installed on it

A mobile run cannot work without a real device and a **resolved, installed**
app-under-test. Do NOT ask the developer to hand you caps and do NOT guess them —
work them out yourself from the device and the repo. Complete every step below
before calling `code run`; if any step can't be satisfied, STOP and tell the
developer what to fix.

1. **Device (required).** List connected devices:

   ```bash
   testsigma list devices --local
   ```

   If none are listed, STOP: ask the developer to connect a device (USB, USB
   debugging on) and confirm the Testsigma Agent (Gen 2) is running — then retry.
   Take the chosen device id as `<id>` (it is also the adb serial).

2. **Locate adb.** The machine often has no `adb` on `PATH`; the agent bundles
   one. Resolve it once:

   ```bash
   ADB="$(command -v adb || echo "$HOME/.testsigma/android/platform-tools/adb")"
   ```

3. **Identify the app package from the repo** (prefer this over asking):
   - Android native / React Native / Flutter — `applicationId` in
     `app/build.gradle` or `android/app/build.gradle(.kts)`; else the `package`
     in `AndroidManifest.xml`.
   - Only if you truly can't find it, ASK the developer for the app package.

4. **Verify the app is installed on the device:**

   ```bash
   "$ADB" -s <id> shell pm list packages | grep -w "package:<pkg>"
   ```

   If this prints nothing, the app is NOT on the device. STOP and ask the
   developer to install it (e.g. `./gradlew installDebug`, or install the APK),
   then retry. Never run against a device that doesn't have the app.

5. **Resolve the launch activity** (don't invent it):

   ```bash
   "$ADB" -s <id> shell cmd package resolve-activity --brief <pkg> | tail -1
   ```

   This prints `<pkg>/<activity>`. Fallback: `"$ADB" -s <id> shell dumpsys package
   <pkg>` and read the activity under `android.intent.action.MAIN` /
   `category.LAUNCHER`.

6. **Build caps and run** — only after device + installed app + activity are all
   known, and the developer has confirmed:

   ```bash
   testsigma code run --input tests/<e2e-dir>/<feature>.spec.ts \
     --device <id> \
     --caps '{"appium:appPackage":"<pkg>","appium:appActivity":"<activity>","appium:noReset":false}'
   ```

   `appium:noReset:false` starts each run from a clean app state; use `true` to
   keep existing data/login.

   **iOS:** the identity is the bundle id — `appium:bundleId` (from the Xcode
   project / `Info.plist` `CFBundleIdentifier`); there is no `appActivity`. Verify
   the app is installed on the target simulator/device the same way before running.

Whatever the type, ask **"To run this I need <X>. Run it now?"** and only run on
yes. Never launch a device run or hit a live web/api target without explicit
confirmation.

## Step 6 — Read the results

Run non-interactively (as you do), `code run` keeps stdout clean and prints a
single JSON summary line, writing the full per-step results to a temp file:

```json
{"resultsFile":"/…/testsigma-run-<ts>.jsonl","logFile":"/…/testsigma-run-<ts>.bt.log","overall":"passed","counts":{"total":N,"passed":N,"failed":N},"durationMs":N}
```

- `overall` (`passed`/`failed`) and a non-zero exit code tell you the outcome;
  `counts` is the tally.
- **On failure, read `resultsFile`** (JSONL — one event per line) to report the
  failing step. Each failed step line carries `description` (the DSL step),
  `errorType` (e.g. `NO_SUCH_ELEMENT`), `message`, and `locator`. Use these to tell
  the developer which step failed and why, then offer to iterate on the spec.
- `logFile` holds the runner's internal engine logs — consult it only for deep
  debugging; it is not needed for normal pass/fail reporting.
