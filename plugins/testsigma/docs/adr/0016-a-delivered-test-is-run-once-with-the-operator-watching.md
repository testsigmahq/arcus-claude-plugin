# A delivered test is run once, with the Operator watching

A Conversion ends at a committed working copy, and nothing in it has ever touched
a browser. So every check this plugin runs is a reading: of the source, of the
Step Map, of the assembled test against both. A locator that names nothing on
the live page, a wait the application needs and the source hid in a helper, test
data that expired — all of these compile, pass preflight, survive a round trip
and fail on first contact.

The CLI now runs a saved test as a **debug run** on an execution agent on the
Operator's machine: it pauses on a failed step instead of going on, and every
continue reloads the test from the server. So the loop is pause, edit the
`.sigma` file, push it, resume — and the failed step runs again with the fix,
without the steps before it running again.

So every delivered test gets a **Copilot Run**: one debug run of that test, in
its own invocation, after its Conversion. A scenario is not finished until its
test has one whose Debug verdict is passed.

## Considered Options

**Folding the run into `convert`** was rejected on the reason ADR-0012 gives for
one Conversion per invocation. A fix loop is exactly the accumulation that rule
forbids: pause reports, source re-reads and edits pile up in front of the
judgement calls the plugin exists to protect. A Copilot Run is its own
invocation, on one test, and stops.

**Letting the run edit freely** was rejected because the fix that makes a step
pass is not always the fix that keeps the test testing what the source tested.
The cheapest way to make a failing assertion pass is to weaken it, and a
weakened assertion passes every run after. So every edit is put to the Operator
before it is pushed, and their answer is recorded beside the edit.

**Bumping the row's Version for every edit** was rejected. Most live fixes are
true of one test and not of the Source Step: a wait this screen needs, a value
this scenario's data wants. A bump returns every test that consumed the row to
`pending`, and re-doing forty delivered tests for one screen's wait moves the
customer's number backwards for nothing.

**Never bumping it** was rejected for the opposite reason. Sometimes the live run
shows the row itself was wrong — the Step Map missed something the helper did,
and every test built on it carries the same defect. That is the thirty-five-reuse
defect in `migration-directory.md`, found late. Recording it against one test
while the row stays `reviewed` would leave the other tests wrong and counted.

## Decision

A live edit is **Drift**, and each one is ruled one of two ways, by the Operator:

- **test-local** — true of this test only. The row's Version stays. The edit is
  recorded against the test, in `drift/<test>.md`, with the Operator's answer.
- **row defect** — true of the Source Step. The row is decided again with map's
  full reading of the helper, its Version is bumped, and the tests that consumed
  the old version re-open through `invalidated_scenarios.py` as they always have.

A re-opened scenario is re-assembled from the Step Map, which knows nothing of
test-local Drift. So its next Copilot Run reads `drift/<test>.md` first and puts
each recorded edit back, with the Operator shown the earlier ruling.

## Consequences

**A Migration now executes tests, in one place.** `cli-probe.md` said a Migration
never executes one. That remains true of every Conversion. The Copilot Run is the
single exception, and it runs only with the Operator present.

**A Copilot Run is a Delivery of one test.** A debug run executes the saved
server test, so the test must be pushed first. ADR-0014 requires that a push be a
moment a person chose; the Operator starts the run and confirms each edit, so
each push is attributable. Every rule in `delivery.md` still applies — a dry run
before every push, no flags, per-upload consent.

**A passed verdict is not Equivalence.** It says the test ran to its end in a
real browser. It does not say the test checks what the source checked, which is
still the Step Map's job and still not observable by running anything.

**The Operator's count gains a second number:** tests delivered of total, and of
those, tests proved by a passed Copilot Run.
