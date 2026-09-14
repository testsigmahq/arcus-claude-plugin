#!/usr/bin/env python3
"""Find the delivered tests a corrected Step Map row has superseded.

`migration-directory.md` has always said that a row failing re-check "stops
being `reviewed` and is worked again, along with every test already assembled
from it". Under whole-suite Phases no test existed when a row was revised, so
nothing ever had to find them. Conversions make the rule reachable, and the only
other way to find those tests is to read the whole working copy — expensive
enough that the rule would quietly go unobeyed.

    invalidated_scenarios.py --suite <suite root> [--apply]

It compares the row versions each `assembled.md` row recorded against the
versions `step-map.md` holds now. A test that consumed an older version was
built on a decision since overturned, and its scenario goes back to `pending` to
be re-taken as a Conversion through the same loop. With `--apply` it writes that
status back; without, it only reports, because a report that rewrites the queue
surprises whoever ran it to look.

Exactness matters in both directions. Returning too many re-does delivered work
and moves the customer's number backwards for nothing; returning too few leaves
a test built on a ruling since overturned inside the delivered count, which is
the one thing that count exists to be honest about.

Exit 0 when every delivered test is current, 1 when anything needs re-taking or
the files it needs are missing.
"""
import argparse
import pathlib
import re
import sys

from migration_tables import is_divider, read, split_cells, table

#: `<source step>@<version>` inside a `Row versions consumed` cell.
CONSUMED = re.compile(r"`([^`]+)`@(\d+)")

PENDING = "pending"

#: Statuses `--apply` will overwrite. A parked scenario keeps its status: it
#: waits on the Operator, a superseded row does not clear that, and overwriting
#: would lose what it waits on. An `out-of-scope` scenario was ruled out by a
#: person, and a version bump does not overturn that ruling.
REOPENABLE = {"done"}


def current_versions(step_map_text):
    """Each Source Step's version as the Step Map holds it now."""
    out = {}
    for row in table(step_map_text):
        step = row.get("Source Step", "").strip().strip("`")
        version = row.get("Version", "").strip()
        if step and version.isdigit():
            out[step] = int(version)
    return out


def consumed(assembled_row):
    """The (Source Step, version) pairs one assembled test recorded."""
    return [(step.strip(), int(version))
            for step, version in CONSUMED.findall(
                assembled_row.get("Row versions consumed", ""))]


def superseded(assembled, versions):
    """(re-openable, anomalies): scenario to the rows that moved under it.

    A consumed version behind the row's current one is the case the rule was
    written for, and those scenarios are re-taken.

    Two others are reported and *not* re-opened, because each means the
    directory says something impossible rather than something superseded: a
    version ahead of the row, and a row the Step Map no longer holds. Neither
    can be fixed by converting the scenario again, and re-opening on one would
    re-do delivered work on a guess about what a person meant.
    """
    reopenable, anomalies = {}, {}
    for row in assembled:
        scenario = row.get("Scenario", "").strip().strip("`")
        for step, version in consumed(row):
            if step not in versions:
                anomalies.setdefault(scenario, []).append((step, version, None))
            elif version > versions[step]:
                anomalies.setdefault(scenario, []).append(
                    (step, version, versions[step]))
            elif version < versions[step]:
                reopenable.setdefault(scenario, []).append(
                    (step, version, versions[step]))
    return reopenable, anomalies


def describe(step, was, now):
    if now is None:
        return f'  "{step}" — the test was built on a decision the Step Map no longer holds'
    if was > now:
        return f'  "{step}" — the test records a later decision ({was}) than the Step Map holds ({now})'
    return f'  "{step}" — decided again since ({was} then, {now} now)'


def reopen(scenarios_text, affected):
    """`scenarios.md` with each affected scenario back at `pending`.

    Rewritten line by line rather than regenerated, so a column the writer added
    and a comment above the table survive. A file that loses a person's edits
    every time a row is corrected is a file they stop writing in. For the same
    reason a `Reason` already on the row is kept after the one written here,
    rather than overwritten: whoever wrote it meant it.

    Only rows of the queue table are touched — lines before its header, and any
    line that is not a row of it, are copied through untouched.
    """
    lines, header = [], None
    for line in scenarios_text.split("\n"):
        if not line.strip().startswith("|"):
            lines.append(line)
            continue
        cells = split_cells(line)
        if header is None and not is_divider(cells):
            header = cells
            lines.append(line)
            continue
        if header is None or is_divider(cells):
            lines.append(line)
            continue
        # Pad to the header before touching a cell: an editor routinely drops a
        # trailing empty one, and a `done` row with no Reason is the common case.
        cells += [""] * (len(header) - len(cells))
        # By header, never by position: a column added ahead of `Status` would
        # otherwise silently rewrite whatever now sits at index two.
        try:
            scenario_at = header.index("Scenario")
            status_at = header.index("Status")
            reason_at = header.index("Reason")
        except ValueError:
            lines.append(line)
            continue
        name = cells[scenario_at].strip("`")
        if name in affected and cells[status_at].lower() in REOPENABLE:
            cells[status_at] = PENDING
            steps = ", ".join(step for step, _, _ in affected[name])
            written = f"Re-opened: {steps} was decided again"
            existing = cells[reason_at]
            cells[reason_at] = f"{written}. {existing}" if existing else written
            lines.append("| " + " | ".join(cells) + " |")
        else:
            lines.append(line)
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", required=True, help="the source suite's root")
    p.add_argument("--apply", action="store_true",
                   help="return the affected scenarios to pending")
    args = p.parse_args()

    migration = pathlib.Path(args.suite) / ".testsigma" / "migration"
    texts, missing = read(migration, "scenarios.md", "step-map.md", "assembled.md")
    if missing:
        print(f"no {missing} in the Migration Directory. Which tests were built on")
        print("which decisions is recorded there, and without it nothing can say")
        print("whether a delivered test is still current — which is not the same")
        print("as saying that it is.")
        return 1

    scenarios_text, step_map_text, assembled_text = texts
    versions = current_versions(step_map_text)
    affected, anomalies = superseded(table(assembled_text), versions)

    if not affected and not anomalies:
        print("Every delivered test was built on the decisions that stand now.")
        return 0

    if affected:
        print(f"{len(affected)} delivered test(s) were built on a decision that has")
        print("since changed, so they are no longer current:\n")
        for scenario, rows in affected.items():
            print(f"{scenario}")
            for step, was, now in rows:
                print(describe(step, was, now))

    if anomalies:
        print("\nThese say something the Migration cannot have produced, so they")
        print("are left exactly as they are for somebody to look at:\n")
        for scenario, rows in anomalies.items():
            print(f"{scenario}")
            for step, was, now in rows:
                print(describe(step, was, now))

    if not affected:
        return 1

    if args.apply:
        (migration / "scenarios.md").write_text(
            reopen(scenarios_text, affected), encoding="utf-8")
        print("\nEach is back in the queue as pending, and is converted again the")
        print("same way as any other scenario. The delivered count drops by that")
        print("many, which is the honest number.")
        return 1 if anomalies else 0
    print("\nNothing has been changed. Re-run with --apply to return these to")
    print("the queue.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
