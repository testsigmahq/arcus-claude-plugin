# Design: running tests from the Arcus plugin (0.8.0)

0.7.0 writes, checks and pushes. `design-authoring-plugin.md` left running out: "the CLI does not run tests". The CLI
now has `arcus run` (CLI 0.1.1). This note says how running joins the flow. Read it with the 0.7.0 design note.

## What `arcus run` is, for the plugin

- It runs **one** web test, in a browser on this machine. Nothing is sent to Arcus. **No sign-in is needed.**
- The browser comes from the local Testsigma agent (`arcus browsers list`). The CLI never finds one itself.
- It runs the same gate as `arcus check` first. A test that does not compile is `refused`, and no browser starts.
- Local `@element` files are used as they are, pushed or not.
- Values for `{env.x}` come from `--base-url` and `--var name=value`. There is no relative `nav`.
- `--json` prints one object: `run.status` is `passed`, `failed`, `refused` or `interrupted`. A failed run has
  `failedStep {description, message, screenshot}` or a `problem`. A time limit is `failed` with the step it was on.
- Exit: `0` passed, `1` failed, refused or interrupted, `3` this machine cannot run it (no agent, no `web` platform, a
  bad option). Never `2`: a run does not touch Arcus.
- Not yet: Android and iOS, datasets, groups, running many tests at once.

## The flow after this version

```text
setup ──► author ──► run ──► push
            ▲         │
            └─ fix ───┘   (a failure that is the test's fault goes back through author's rules)
```

Every skill ends by naming the next one and stops there. Each keeps its own gate:

| Skill | Gate before it acts |
|---|---|
| `setup` | none: it only reads, and writes only after a yes |
| `author` | none: it writes files, and the CLI judges them |
| `run` | the user asked to run, or said yes to the offer. The user has seen the address the test opens |
| `push` | a dry run the user has seen, and a yes for this push |

Run is not a gate for push. A push of a test that was never run is allowed. `push` says once that the test was not run
here and offers `/arcus:run`. The user decides.

## Decisions

1. **A new skill, `run`, not a step inside `author`.** Authoring and running fail for different reasons and end in
   different places. A skill that does both grows past its budget and hides which gate applies. `author` keeps one job:
   a file the CLI accepts. `run` has one job: say what happened when the test ran.
2. **The user's request to run is the consent.** A local run is not a push: it changes nothing in Arcus. It does reach a
   live address, so the skill names every address before it starts, and never runs against one the user has not seen.
3. **`run` does not need sign-in, and it must not send the user to `/arcus:setup` for one.** It needs the CLI (0.1.1
   or newer), a bound project, and the agent. A missing project goes to `setup`. A missing agent is the user's to fix.
4. **Secrets never go into the command.** `--var name=value` shows in the transcript and the shell history. A value that
   is secret is passed as `--var name="$SHELL_VARIABLE"` that the user set in their own terminal. The skill never
   reads `.env*`, never asks for a password in chat, and never invents a value. A non-secret value (an address, a
   username for test data) is fine.
5. **The result is read from `--json`, not from the exit code alone.** Exit `1` covers three different things. The skill
   reads `run.status`, then the step, the message, and the screenshot. It looks at the screenshot (Claude can read an
   image file): the page is the evidence for a locator that did not match.
6. **A failure has one of three owners, and the skill says which before it edits anything.**
   - *The test is wrong* (a locator that does not exist in the app, a wrong expected text, a missing wait): fix it, with
     the rules of `author` and `references/editing.md`, then `check`, `fmt`, run again.
   - *The app is wrong* (the test says what the app should do, and the app does not): that is a finding for the user.
     Report it. Do not change the test to match a bug.
   - *The setup is wrong* (address unreachable, a variable with no value, a browser that cannot start): tell the user.
   When the evidence does not decide, show it and ask. Never guess which side is right.
7. **A fix loop has a limit.** At most three rounds of fix and run. Stop at once when the same step fails with the same
   message twice. Then show what is known. Do not loop.
8. **The rule from `author` still holds, and now matters more.** A run is the first time the test meets the app. Never
   delete a `verify`, loosen an expected value to the value the app showed, or add a wait to hide a fault unless the user
   confirms that the app is right.
9. **One test per run, so many tests are many runs.** The skill runs them one after another and reports one line each. It
   never claims a suite result.
10. **Headless by default.** `--headed` only when the user asks to watch, or to debug a failure the screenshot cannot
    explain, and then it says a window opens.
11. **`setup` gains one non-blocking line: can this machine run tests?** `arcus browsers list` and the project's
    platforms. A failure here never stops authoring or pushing. It says what to do, and that it matters only for run.
12. **Version 0.8.0.** A new skill is a minor. The plugin needs CLI 0.1.1 or newer for `/arcus:run`. The other skills still
    work on CLI 0.0.x. `setup` proves the CLI has `run` by calling `arcus run --help`.

## What changes

| File | Change |
|---|---|
| `skills/run/SKILL.md` | new |
| `references/running.md` | new: the result shape, failure owners, how to read a screenshot, the options |
| `skills/author/SKILL.md` | no longer "cannot run": ends with the offer to run; hands over to `run` when the user asked to verify |
| `skills/push/SKILL.md` | the "not run" lines: say once that the test was not run here, offer `/arcus:run`; no longer "never runs tests" |
| `skills/setup/SKILL.md` | the CLI must have `run`; one non-blocking readiness line for running |
| `references/platforms.md`, `reading-the-app.md` | mobile cannot run yet (says so, with the CLI's reason); env names a test reads |
| `commands/help.md`, `README.md` | the new skill, the new flow, the CLI version, "This version" rewritten |
| `plugin.json`, `design-authoring-plugin.md` | 0.8.0; the "skipped for now" section points here |
| `tests/` | the new skill and the CLI surface (`run`, `browsers list`); a test that every `/arcus:<skill>` named in any document exists, and that the flow graph above is the one the documents describe; a test that no document still says the plugin cannot run tests |
| `evals/` | new cases that need the real CLI: see below |

## Evals

0.7.0 deferred evals until the run version. These are the cases that prove the skills steer Claude, which document
tests cannot. They use `file:` pages, so no server is needed. They need the `arcus` CLI (0.1.1 or newer) on `PATH` and,
for the cases that open a browser, the Testsigma agent running. Run them with `claude plugin eval plugins/arcus`.

| Case | Proves |
|---|---|
| `run-a-passing-test` | `/arcus:run` runs the test and reports passed, browser and time, then offers push |
| `run-a-wrong-expectation` | reads the failed step and the screenshot, names the owner, and does not delete the `verify` |
| `author-then-run` | "write a test and run it" goes through `author`, then `run`, and the test was run |
| `run-a-mobile-project` | says device runs are not supported, and does not edit `arcus.json` to get around it |
| `run-needs-a-secret` | a test reading `{env.password}` is not run with an invented or typed value |

## Out of scope

The migration plugin (`plugins/testsigma`), the other editors' plugins, `pull`, datasets and groups, running on devices,
and pushing run results to Arcus (the CLI has no such command).
