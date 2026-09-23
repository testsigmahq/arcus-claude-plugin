---
name: copilot
description: Use when a Migration's delivered test should be proved against a real browser — running a converted test live, fixing it step by step where it fails, or finishing a scenario whose Conversion is done but whose test has never run. Not the way into a Migration and not a substitute for convert — this runs one already-assembled test as a debug run on this machine's execution agent, puts every proposed edit to the Operator before it is pushed, records each accepted edit as test-local Drift or a row defect, and stops with the Debug verdict.
---

# Copilot: one delivered test, run live

A Copilot Run is one debug run of one test a Conversion already delivered. The
test runs on the execution agent on the Operator's machine, pauses where a step
fails, and waits. You find why, propose an edit, and the Operator decides. An
accepted edit is pushed, the failed step runs again with it, and the steps before
it do not. At the end the run is stopped and judged. ADR-0016 records why every
delivered test gets one.

A scenario is not finished until its test has a Copilot Run whose Debug verdict
is passed. `convert` delivers the test; this proves it runs.

**Who you are talking to.** The person running a Migration is the Operator. They
know Testsigma and do not necessarily read code, so nothing you put in front of
them carries code, a file path, a stack trace or a diagnostic code. Those go in
the Migration Directory. They are copied here rather than pointed at because a
question arises mid-work; `${CLAUDE_PLUGIN_ROOT}/references/asking.md` decides
them and covers everything else shown to the Operator. See
`${CLAUDE_PLUGIN_ROOT}/CONTEXT.md` for the vocabulary this plugin uses with them.

The files this reads and writes — `runs/<test>.md` and `drift/<test>.md` among
them — are defined in `${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`.

## One test per invocation, and then stop

**Run exactly one test and end the session's work.** Do not take the next test,
and do not offer to. The reason is the one `convert` gives: pause reports, source
re-reads and edits accumulate, and the judgement this skill exists for — whether
an edit keeps the test testing what the source tested — is the one that fails
quietly when it is made far down a crowded context.

## Before anything

**A Migration must have been surveyed and a Conversion delivered.** If
`.testsigma/migration/` is absent, stop and say the suite has not been surveyed.
If no scenario is `done`, there is nothing to run: say so, and that `convert`
delivers the first test.

**The build must have a debug run.** Follow
`${CLAUDE_PLUGIN_ROOT}/references/cli-probe.md`. Where the help lists no
`test debug`, stop: tell the Operator this build cannot run a test live, and
record in `check-record.md` that the delivered tests are not covered by a live
run — never that they passed one, per
`${CLAUDE_PLUGIN_ROOT}/references/checks.md#a-check-that-could-not-run-is-not-checked`.

**An execution agent must be running on this machine.** Run
`testsigma agents list --json`. Where none is marked as this machine, stop and
ask the Operator to start the Testsigma agent app. Do not pick another machine's
agent: the Operator watches this browser, and a run nobody sees is not the run
ADR-0016 describes.

## Step 1: Take the next test

Run `${CLAUDE_PLUGIN_ROOT}/scripts/copilot_status.py --suite <the suite>`. It
names the delivered test with no passed Copilot Run since it was last assembled,
oldest first, and that is the test this run proves. The Operator naming a test
overrides it.

Oldest first because a row defect is cheapest found early. A wrong row found in
the third test has three dependents; found in the fortieth, it has forty.

## Step 2: Put back recorded Drift

Where `drift/<test>.md` already holds test-local edits, this test was assembled
again from the Step Map since they were made, and the Step Map knows nothing of
them. Re-apply each one to the working copy before the run. Name each to the
Operator with its earlier ruling, and ask whether it still stands. A retracted
edit gets a row saying so; it is never deleted.

## Step 3: Push the test, with the Operator

A debug run executes the **saved** test on the server, never the local file. So
the test is pushed first, and this is a Delivery of one test.
`${CLAUDE_PLUGIN_ROOT}/references/delivery.md` governs it whole: step groups the
test calls go before it, `--dry-run` runs before every push, no flag is passed,
and a new version of an existing upload needs its own consent.

Put the dry run's plan to the Operator in their terms and wait for a yes before
the first push. Their starting this run is not that yes.

## Step 4: Start the run

`testsigma test debug <file> --json`. Add `--environment` where the test uses
environment variables. The first pause report comes back when the run pauses.
Where it reports that setup is holding the start back, tell the Operator what it
says; do not retry around it.

## Step 5: At each pause

Read `pause.step`. Where its `result` is a failure, open the step at
`source.path:line` and find the cause before proposing anything. There are three,
and they are ruled differently.

**The test does not fit the live application.** A locator that finds nothing, a
wait the page needs, a value this scenario's data wants. Propose the edit.

**The Step Map row is wrong.** The failure shows the row missed something the
source does — the helper waited, retried, or checked a thing the row did not
carry. Before proposing anything, give the row the reading `map` gives it: open
the helper and compare it against the expression, per
`${CLAUDE_PLUGIN_ROOT}/references/fault-classes.md#conducting-the-comparison`.

**The application is wrong.** A real defect, or an environment that is down.
Nothing in the test should change. Say what you saw, record it in
`application-facts.md`, and ask the Operator whether to skip the step or stop.

**Put every edit to the Operator before it is written.** Say which step failed
and what it did, what the edit is, why, and whether it changes what the step
checks. Propose the ruling — test-local or row defect — and let them decide it.
Nothing is pushed on your own judgement.

**Never weaken what a step checks to make it pass.** Loosening an assertion,
changing an expected value, or dropping a check makes every later run pass and
tests nothing. Such an edit is proposed only when the source's expectation is no
longer true of the application, and is recorded with `yes` under what it
changes. A weakened check nobody can find again is a Divergence.

When the Operator agrees:

1. Write the Drift row first — before the push, so a session that ends mid-push
   has still recorded what was agreed.
2. Edit the working copy, dry-run, and push.
3. `testsigma test debug resume --json`. The failed step runs again with the
   edit; `(try N)` counts the tries.

A pause report that says the file has changes not pushed means the session is
running the old copy. Push, then resume.

**Stop proposing after three tries of one step.** Say what was tried and ask the
Operator whether to skip it. `testsigma test debug skip-over` marks it not run
and pauses before the next. A skipped step makes the verdict `stopped`, and the
test is not proved.

Use `testsigma test debug break <step-id>` to stop before a step you want to see,
by the id the pause report prints.

## Step 6: End the run and read the verdict

**A debug run never ends by itself.** At the test's last step it holds, paused,
and the pause report says so with `pause.atEnd` true. Until `stop`, the run is
still running and has no verdict. So at `atEnd`, run
`testsigma test debug stop`, then `testsigma test debug result --json`
straight away. Starting another debug run of this test deletes this run's step
results, so the verdict is read before anything else starts. The session record
is kept after `stop`, so `result` needs a run's id only where that record is
gone.

Take the verdict from the result's `verdict` field, and nothing else. `failed`
and `stopped` both exit 3, so the exit code cannot tell them apart. A `result`
with no verdict means the run has not ended, or a newer run of this test removed
its step results; it is never recorded as any verdict.

- **passed** — every step's last try passed. The test is proved.
- **failed** — a step's last try failed.
- **stopped** — not every step ran, and nothing failed.

Write the run's row in `runs/<test>.md` before anything else.

A marker block standing for Residue is not a failure to fix. It is a step
declined on purpose, and the run stepping over it is correct.

## Step 7: Where a row defect was ruled

Decide the row again in `step-map.md` and bump its `Version`, per the Migration
Directory reference. Set this test's consumed version in `assembled.md` to the
new one — it was proved live with the corrected expression.

Then run `${CLAUDE_PLUGIN_ROOT}/scripts/check_row_versions.py --suite <the suite>`
and `${CLAUDE_PLUGIN_ROOT}/scripts/invalidated_scenarios.py --suite <the suite>
--apply`. The other tests built on the old ruling return to `pending`, and each
gets its own Conversion and its own Copilot Run.

## Step 8: Commit

Run `${CLAUDE_PLUGIN_ROOT}/scripts/check_committed.py --suite <the suite>` and
commit what it lists: the Migration Directory and the working copy together.

## Step 9: Report, and stop

Tell the Operator, in this order:

- the test, by its scenario's name, and its Debug verdict
- **tests proved of tests delivered**, from `copilot_status.py`
- each edit made, with its ruling — test-local, or a row defect and the tests
  it re-opened
- any edit that changes what a step checks, named on its own
- any step skipped, and why
- anything recorded about the application

Say plainly that passed means the test runs, not that it checks everything the
source checked. That is still the Step Map's work.

Then stop.
