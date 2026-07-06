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

## Step 5 — Offer to run (gather target, then confirm)

`testsigma code run` executes tests for **all three** types — web, api, and mobile.
Tell the developer what the detected type needs, then ask before executing:

- **web** — a base URL (a running dev server or a deployed site). Offer to detect
  an obvious local dev-server port. Once the target is confirmed:

  ```bash
  testsigma code run --input tests/<e2e-dir>/<feature>.spec.ts
  ```

- **api** — the API base URL and any required env (e.g. `API_PASSWORD`). Then run
  the same `testsigma code run --input tests/<e2e-dir>/<feature>.spec.ts`.

- **mobile** — list devices and pick one, then gather Appium caps:

  ```bash
  testsigma list devices --local
  ```

  Run with the chosen device id and caps (the agent supplies the Appium URL + udid):

  ```bash
  testsigma code run --input tests/<e2e-dir>/<feature>.spec.ts \
    --device <id> \
    --caps '{"appium:appPackage":"...","appium:appActivity":"...","appium:noReset":false}'
  ```

Whatever the type, ask **"To run this I need <X>. Run it now?"** and only run on yes.
Never launch a mobile/device run or hit a live web/api target without explicit
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
