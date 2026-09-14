#!/usr/bin/env python3
"""Check that a re-decided Step Map row had its `Version` bumped.

The version is the whole mechanism by which a corrected row's dependents are
found: `assembled.md` records what each delivered test consumed, and a test
whose recorded version is behind the row's current one was built on a decision
since overturned. A row re-decided without a bump is therefore invisible — every
test built on the old ruling keeps its place in the delivered count, and nothing
anywhere says otherwise.

    check_row_versions.py --suite <suite root> [--against HEAD]

It compares `step-map.md` in the working tree against the committed one and
rejects two things:

- a row whose Expression or Status changed while its Version did not, which is
  the invisible correction above;
- a row whose Version changed while its Expression and Status did not, which
  returns scenarios to `pending` and re-assembles tests for a correction nobody
  built anything on. Occurrence counts and provenance change every Conversion.

A row that is new, or gone, is neither: there is nothing to compare it with.

Exit 0 when every row agrees with its version, 1 when one does not or the
comparison cannot be made.
"""
import argparse
import pathlib
import subprocess
import sys

from migration_tables import table

STEP_MAP = ".testsigma/migration/step-map.md"

#: What a Version speaks for. Everything else on a row — occurrences, source,
#: parameter shapes — is bookkeeping that changes as new scenarios reach it.
DECIDED_BY = ("Expression", "Status")


def committed(root, revision, path):
    """The committed text of a file, or None when there is no committed copy."""
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{revision}:{path}"],
        capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def rows_by_step(text):
    out = {}
    for row in table(text):
        step = row.get("Source Step", "").strip().strip("`")
        if step:
            out[step] = row
    return out


def faults(before, now):
    """Rows whose version and whose decision disagree about what changed."""
    out = []
    for step, row in now.items():
        was = before.get(step)
        if was is None:
            continue
        decided_again = any(
            was.get(field, "").strip() != row.get(field, "").strip()
            for field in DECIDED_BY)
        bumped = was.get("Version", "").strip() != row.get("Version", "").strip()
        if decided_again and not bumped:
            out.append(f'"{step}" has been decided again and its version has not '
                       "moved. Every test already built on the old decision goes "
                       "on counting as delivered, and nothing can find them.")
        elif bumped and not decided_again:
            out.append(f'"{step}" has a new version and the same decision. That '
                       "returns scenarios to the queue and rebuilds their tests "
                       "for a correction nobody built anything on.")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", required=True, help="the source suite's root")
    p.add_argument("--against", default="HEAD",
                   help="the revision to compare the working tree with")
    args = p.parse_args()

    root = pathlib.Path(args.suite)
    working = root / STEP_MAP
    if not working.exists():
        print("no step-map.md in the Migration Directory. What has been decided")
        print("lives there, and a file that cannot be read is not a file with")
        print("nothing wrong in it.")
        return 1

    before = committed(root, args.against, STEP_MAP)
    if before is None:
        print("Nothing to compare with: the Step Map has not been committed yet,")
        print("so no row can have been decided twice. Commit as each Conversion")
        print("ends and this reads what changed since.")
        return 0

    problems = faults(rows_by_step(before),
                      rows_by_step(working.read_text(encoding="utf-8")))
    if not problems:
        print("Every row decided again since the last commit has a new version.")
        return 0

    print(f"{len(problems)} row(s) disagree with their own version:\n")
    for problem in problems:
        print(f"- {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
