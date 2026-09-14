#!/usr/bin/env python3
"""Check that the Conversion queue says one thing about each scenario.

`scenarios.md` is both the incidence and the queue, and every number an Operator
is given comes off it: tests delivered of total scenarios, what is parked and
what it waits on, what was ruled out. None of those survives a row that
contradicts itself, and none of the contradictions announces itself — each reads
as a perfectly ordinary row until someone counts.

    check_scenarios.py --suite <suite root>

It rejects a scenario that is `done` with nothing in `assembled.md` to show for
it, one that is `parked` or `out-of-scope` with no `Reason`, one holding a status
outside the four — which is what two statuses in one cell reads as — and one
listed twice at all, whether or not the two rows agree. Two rows that agree are
still two rows, and the totals count both.

Every failure is reported, not the first. A check that has to be re-run once per
rejection is a check people stop running.

Exit 0 when the queue is consistent, 1 when it is not or the files are missing.
"""
import argparse
import pathlib
import sys

from migration_tables import read, table

#: The complete set. `resume` counts the rows in each state, so a private fifth
#: value is counted as none of them and silently leaves the totals short.
STATUSES = ("pending", "done", "parked", "out-of-scope")

#: Both say a scenario is not being worked now, and neither is readable without
#: what it waits on or why it was ruled out.
NEEDS_REASON = ("parked", "out-of-scope")


def assembled_scenarios(assembled_text):
    return {row.get("Scenario", "").strip().strip("`")
            for row in table(assembled_text)}


def faults(scenarios, assembled):
    """Every contradiction in the queue, as lines an Operator can act on."""
    out = []
    for row in scenarios:
        name = row.get("Scenario", "").strip().strip("`")
        status = row.get("Status", "").strip().lower()
        reason = row.get("Reason", "").strip()
        if not name:
            continue
        if not status:
            out.append(f'"{name}" has no status, so nothing counts it at all.')
            continue
        if status not in STATUSES:
            named = ", ".join(STATUSES)
            out.append(f'"{name}" is {status}, which is not one of {named}. '
                       "A status outside those four is counted as none of them.")
            continue
        if status == "done" and name not in assembled:
            out.append(f'"{name}" is delivered, but no test is recorded against it. '
                       "It is being counted in the tests delivered and there is "
                       "nothing to show for it.")
        if status in NEEDS_REASON and not reason:
            waiting = "what it is waiting on" if status == "parked" else "why it was ruled out"
            out.append(f'"{name}" is {status} with no reason, so nobody can tell '
                       f"{waiting}.")
    return out


def duplicates(scenarios):
    """Scenarios listed more than once, however their rows read.

    Differing statuses are the loud case: whichever a reader takes, the other is
    wrong. Agreeing ones are counted here too, because every total is a count of
    rows, and one scenario counted twice makes both the delivered number and the
    denominator wrong by one.
    """
    by_name = {}
    for row in scenarios:
        name = row.get("Scenario", "").strip().strip("`")
        if name:
            by_name.setdefault(name, []).append(row.get("Status", "").strip().lower())
    return {name: statuses for name, statuses in by_name.items()
            if len(statuses) > 1}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", required=True, help="the source suite's root")
    args = p.parse_args()

    migration = pathlib.Path(args.suite) / ".testsigma" / "migration"
    texts, missing = read(migration, "scenarios.md", "assembled.md")
    if missing:
        print(f"no {missing} in the Migration Directory. The queue and what has")
        print("been delivered are both recorded there, and a queue that cannot be")
        print("read is not a queue with nothing wrong in it.")
        return 1

    scenarios_text, assembled_text = texts
    scenarios = table(scenarios_text)
    problems = faults(scenarios, assembled_scenarios(assembled_text))
    for name, statuses in duplicates(scenarios).items():
        reads = " and as ".join(sorted(set(statuses)))
        tail = ("Whichever a reader takes, the other one is wrong."
                if len(set(statuses)) > 1
                else "Every total counts rows, so this one is counted twice.")
        problems.append(f'"{name}" is listed {len(statuses)} times, as {reads}. {tail}')

    if not problems:
        print(f"{len(scenarios)} scenarios, and each says one thing about itself.")
        return 0

    print(f"{len(problems)} thing(s) in the queue contradict themselves:\n")
    for problem in problems:
        print(f"- {problem}")
    print("\nEvery progress number comes off this table, so each of these is a")
    print("number somebody would be given wrongly. Correct them before reporting.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
