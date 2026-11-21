---
name: prove
description: Use when work on an issue in a qi-mode project is ending, before you tell the developer the work is finished, or when the developer asks ("prove CW-412", "is CW-412 covered", "check the issue before I merge", "are we done"). Writes the missing tests, runs every case of the issue on this machine, gives a gap report (covered, failing, missing, local only, rejected, not verified, and the additions), and proposes a push of every test. Qi mode only. Sends nothing without a yes. Not for one test (use run).
---

# Prove: show the gaps between the code and the expectation

QI's cases say what the issue expects. At the end of the work you check the code against them on this machine, tell the developer what is covered and what is not, and propose to send the tests to QI, so that QA and the PM see the result. The rules of the layer are in `${CLAUDE_PLUGIN_ROOT}/references/layer.md`. The command and the shape of the report are in `${CLAUDE_PLUGIN_ROOT}/references/verifying.md`.

In a direct project `arcus issue verify` stops with exit `3`: say prove is a QI flow (`/arcus:mode`). Not signed in (exit `2`): `/arcus:setup`.

## 1. Start

Start before you tell the developer the work is finished, or when the developer asks. For an issue that has cases, verification is the default. If the developer says "skip", skip it and say that nothing was verified.

Read the expectation you kept from `/arcus:align` first: the issue and the steps of every case. If you lost them, read them again (`arcus issue show <KEY> --json`, then `arcus case show <id> --json`). If no issue is known, ask once.

**No cases.** Do not stop. QI gives no expectation. Say so, tell what you built against the Jira text, and list it as additions. Nothing is verified against QI.

## 2. Tests for the cases

You can write a test for every case that has no file, is in `REWORK`, or has a `suggestion`, through `/arcus:author`. The test covers every step of the case. A step the language cannot express is a gap: say it, do not drop it. You may also write the tests earlier, while you build. When is your choice.

## 3. Run every case

The developer provides the running build. How the app is built or started is the developer's choice: ask when you do not know. Run the issue as `${CLAUDE_PLUGIN_ROOT}/references/verifying.md` says (`arcus issue verify <KEY>`), on the address and platform the user has seen. A single failing file can be run alone with `/arcus:run`.

When a case fails, find the owner first, with the screenshot, as `/arcus:run` says. You can then:

| Owner | A useful move |
|---|---|
| The code of this change | Fix the code, run again |
| The test: a locator, a wait, the setup of the test | Repair the test with `/arcus:author`'s rules, run again |
| The case: the app now does on purpose what the case says it should not | An intent change. Do not edit the step or the `verify`. Leave the test failing and list it |
| The setup | Say what to fix. The case is **not verified** |
| The evidence does not decide | Show it and ask |

A fix loop is a suggestion. The developer can stop with failures. A change is on purpose only when the diff, a commit message or the story says so. Otherwise it is a finding.

**Never weaken a test to make it pass.** No deleted `verify`, no removed step, no expected value changed to what the app showed, no wait added to hide a fault, even if the user says the app is right: for a case, that is the case owner's call in QI.

## 4. The gap report

Give it before you say the work is finished. One verdict for each case of the issue, not only the touched ones: **covered**, **failing** (the failed step and the cause: code, test or setup), **missing**, **local only**, **rejected**, **not verified** (with the reason). Then the intent changes, and the list of **additions**: behaviour that no case and no acceptance criterion asks for. The shapes are in `references/verifying.md`. How you keep the report is your choice.

"Done" is every case covered, or the developer says it is done. A failure does not block.

A session that is closed (`sessionClosed`; a sprint or an ad hoc session): prove verifies and reports, and says that QI takes no new versions there, so there is nothing to push. The developer may choose an open session (`arcus issue show <KEY> --session <id or human id>`). If the issue is in several sessions, the developer chooses one first, as `/arcus:align` says. In an ad hoc session, report the cases of `this_issue` and `unknown` as the expectation, and name the `other_issue` cases apart.

## 5. Propose the push

Propose a push of every test of the issue: passing, failing and new ones. A `local only` test goes as a new case (`--new`), so that a PM or QA can review it. A failed run can be pushed: QA and the PM then see the failure. Hand over to `/arcus:push`. Its dry run and the developer's yes apply to every push.

After the push, a reviewer (QA or a PM) accepts or rejects each test in QI.

## Never

- Weaken a test, or hide a gap, a failure or a case that did not run.
- Say a case passes when it was `local only`, `missing` or `not verified`.
- Push without the developer's yes.
- Edit a step or a `verify` of a case to match what the app now does.
- Sign in, or edit `arcus.json`, `arcus.lock` or `.arcus/`.
