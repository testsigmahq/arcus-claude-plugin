#!/usr/bin/env python3
"""Which delivered tests a Copilot Run has proved, and which is run next.

ADR-0016 makes a live run part of finishing a scenario: `convert` delivers the
test, and a Copilot Run whose Debug verdict is passed proves it runs. That adds a
second number to the one the Operator counts — tests proved of tests delivered —
and a number worked out by reading the per-test documents by eye is the number
that drifts from session to session.

    copilot_status.py --suite <suite root>

A delivered test is a `done` scenario with a row in `assembled.md`. It is proved
when the latest row of `runs/<test>.md` reads `passed` **and** that run started
on or after the test's `Assembled` date. The date matters: a re-opened scenario
is assembled again, and a pass recorded before that proved a test that no longer
exists. Counting it would keep the number up while the test it counts has never
run.

The next test is the unproved one assembled longest ago. Oldest first because a
row defect is cheapest found early — found in the third test it has three
dependents, found in the fortieth it has forty.

Exit 0 when every delivered test is proved, 1 when any is not or the files it
needs are missing.
"""
import argparse
import pathlib
import sys

from migration_tables import read, table

DONE = "done"
PASSED = "passed"


def stem(test_cell):
    """`<test>` as the per-test documents spell it: the Test cell, no `.sigma`."""
    name = test_cell.strip().strip("`")
    return name[: -len(".sigma")] if name.endswith(".sigma") else name


def day(cell):
    """The date part of a cell, for comparison. ISO dates sort as text."""
    return cell.strip()[:10]


def latest_run(migration, test):
    """The last row of `runs/<test>.md`, or None where the test never ran."""
    path = migration / "runs" / f"{test}.md"
    if not path.exists():
        return None
    rows = table(path.read_text(encoding="utf-8"))
    return rows[-1] if rows else None


def standing(assembled_on, run):
    """One of: never run, stale, passed, or the verdict that was not a pass."""
    if run is None:
        return "never run"
    if day(run.get("Started", "")) < day(assembled_on):
        return "stale"
    verdict = run.get("Verdict", "").strip().lower()
    return PASSED if verdict == PASSED else (verdict or "no verdict recorded")


def delivered(scenarios_text, assembled_text):
    """(scenario, test, assembled date) for every done scenario, oldest first.

    A `done` scenario with no `assembled.md` row is not listed here; it is the
    contradiction `check_scenarios.py` owns, and reporting it twice would give
    it two owners.
    """
    done = {r.get("Scenario", "").strip().strip("`")
            for r in table(scenarios_text)
            if r.get("Status", "").strip().lower() == DONE}
    out = []
    for row in table(assembled_text):
        scenario = row.get("Scenario", "").strip().strip("`")
        if scenario in done:
            out.append((scenario, stem(row.get("Test", "")),
                        row.get("Assembled", "").strip()))
    # Stable on ties, so two sessions name the same test.
    return sorted(out, key=lambda r: day(r[2]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", required=True, help="the source suite's root")
    args = p.parse_args()

    migration = pathlib.Path(args.suite) / ".testsigma" / "migration"
    texts, missing = read(migration, "scenarios.md", "assembled.md")
    if missing:
        print(f"no {missing} in the Migration Directory. Which tests were")
        print("delivered is recorded there, and without it nothing can say which")
        print("have been proved — which is not the same as saying none have.")
        return 1

    tests = delivered(*texts)
    if not tests:
        print("No test has been delivered yet, so there is nothing to run live.")
        return 1

    proved, unproved = [], []
    for scenario, test, assembled_on in tests:
        state = standing(assembled_on, latest_run(migration, test))
        (proved if state == PASSED else unproved).append((scenario, test, state))

    print(f"{len(proved)} of {len(tests)} delivered test(s) proved by a live run.")
    if not unproved:
        return 0

    print("\nNot yet proved:")
    for scenario, test, state in unproved:
        print(f"  {scenario} ({test}) — {state}")
    scenario, test, _ = unproved[0]
    print(f"\nNext to run: {scenario} ({test})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
