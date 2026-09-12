#!/usr/bin/env python3
"""Materialise each case's fixtures inside its own directory.

`claude plugin eval` refuses an `add_dirs` entry containing `..`:

    path "../fixtures/migration-part-done" escapes the case directory
    (`..` or an absolute path) — it must name something inside it

That settles a question `README.md` recorded as open. The cases were written to
share one copy of each fixture, which is what keeps a fixture and the pytest
suite that also reads it from drifting apart. The runner will not have it, so
the copies live in the cases and `../tests/test_evals.py` asserts they are
byte-identical to the canonical ones. Drift becomes a test failure rather than a
case that quietly tests a fixture nothing else has seen.

Run after changing a canonical fixture:

    python3 evals/sync-fixtures.py
"""
import pathlib
import shutil
import sys

EVALS = pathlib.Path(__file__).resolve().parent
PLUGIN = EVALS.parent

#: basename -> the one true copy. The basename is kept in the case directory so
#: a prompt naming the suite by folder still reads correctly.
CANONICAL = {
    "migration-part-done": EVALS / "fixtures" / "migration-part-done",
    "cucumber-java": PLUGIN / "tests" / "fixtures" / "cucumber-java",
    "tosca-subset-export": PLUGIN / "tests" / "fixtures" / "tosca-subset-export",
}


def cases():
    return sorted(p.parent for p in EVALS.glob("*/case.yaml"))


def wanted(case):
    """Which fixtures a case's scaffold copies, by basename.

    Read from scaffold.sh, not case.yaml. The names lived in case.yaml's
    `add_dirs` until the first real run showed add_dirs does not seed the
    workspace; this script kept reading the old key and cheerfully refreshed
    nothing, reporting "0 fixture copies refreshed" as though that were a
    result. The drift test caught it — a sync script that silently syncs
    nothing is the same shape of fault as a gate that watches the wrong path.
    """
    text = (case / "scaffold.sh").read_text(encoding="utf-8")
    return [name for name in CANONICAL if f"fixtures/{name}/" in text]


def main():
    changed = 0
    for case in cases():
        for name in wanted(case):
            target = case / "fixtures" / name
            if target.exists():
                shutil.rmtree(target)
            target.parent.mkdir(exist_ok=True)
            shutil.copytree(CANONICAL[name], target)
            changed += 1
            print(f"{case.name}/fixtures/{name}")
    print(f"{changed} fixture copies refreshed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
