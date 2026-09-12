#!/usr/bin/env python3
"""Report work that exists only in the working tree at the end of a stage.

Two stages instruct a Migration to commit as it goes, in plain words, and a
measured run followed both and committed nothing — leaving a Migration
Directory and a pushed test in the working tree only. The instruction was not
the problem; an instruction a reader believes they followed is not a check.

Uncommitted work is worse here than in ordinary development because the
Migration Directory *is* the state. A resumed session reads it to decide what is
already done, and cannot tell a row someone reviewed and committed from one a
dead session half-wrote. Git history is the only thing that separates them, and
a stage that ends without committing leaves the next session to guess.

It also covers the working copy, not just the directory. Both stages said to
commit "scoped to the Migration Directory", which would have left the assembled
.sigma files behind even if it had run.

The working copy's path is *read*, never assumed. An earlier version watched a
hardcoded `tests/testsigma`; against a run that had written to a sibling
directory it reported two modified files and missed more than forty untracked
.sigma files. A gate saying "nearly clean" over an entirely untracked working
copy is the fault class it exists to catch, reproduced inside the gate. ADR-0011
makes the path a recorded fact, so this reads `migration.md` for it and says so
when the line is missing rather than falling back silently.

    check_committed.py --suite <suite root>

Exit 0 when the tree is clean, 1 when it is not.
"""
import argparse
import pathlib
import re
import subprocess
import sys

MIGRATION = ".testsigma/migration"
DEFAULT_WORKING_COPY = "tests/testsigma"

#: `Working copy: <path>` in migration.md, per ADR-0011. Anchored to the line so
#: a mention of the phrase in prose elsewhere in the file cannot supply it.
WORKING_COPY = re.compile(r"^Working copy:\s*(\S.*?)\s*$", re.M)


def working_copy(root):
    """The recorded working-copy path, and whether it was recorded at all.

    Returns (path, recorded). A missing line is reported, not silently
    defaulted: the whole point of ADR-0011 is that an unrecorded path is one a
    resumed session cannot find, and a gate that quietly guesses right on this
    machine hides that from the session that guesses differently.
    """
    marker = root / MIGRATION / "migration.md"
    try:
        found = WORKING_COPY.search(marker.read_text(encoding="utf-8"))
    except OSError:
        return DEFAULT_WORKING_COPY, False
    if not found:
        return DEFAULT_WORKING_COPY, False
    path = found.group(1)
    # A placeholder skeleton is not a recorded decision.
    if path.startswith("<"):
        return DEFAULT_WORKING_COPY, False
    return path.strip("/"), True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", default=".")
    args = p.parse_args()
    root = pathlib.Path(args.suite).resolve()
    copy_path, recorded = working_copy(root)
    watched = (MIGRATION, copy_path)

    try:
        out = subprocess.run(
            # -uall, not the default. git collapses an entirely untracked
            # directory to one entry — `?? tests/` — and a substring test for
            # "tests/testsigma" does not match "tests/". That is how this gate
            # reported two modified files while forty untracked .sigma files
            # sat under a directory it never saw named. The collapse is worse
            # the more work is uncommitted, which is backwards for a gate.
            ["git", "-C", str(root), "status", "--porcelain", "-uall"],
            capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"cannot read git status under {root}: {e}")
        print("The Migration's state lives in git history; without it a resumed")
        print("session cannot tell reviewed work from a half-written session.")
        return 1

    dirty = []
    for line in out.splitlines():
        path = line[3:].strip().strip('"')
        if any(w in path for w in watched):
            dirty.append(line.rstrip())

    if not recorded:
        print(f"migration.md records no 'Working copy:' line; watching "
              f"{DEFAULT_WORKING_COPY} as a guess (ADR-0011).")
        print("A path nothing recorded is one a resumed session cannot find, and")
        print("this gate cannot tell a clean tree from a working copy it never saw.")

    if not dirty:
        print(f"nothing uncommitted under {MIGRATION} or {copy_path}.")
        return 0

    print(f"{len(dirty)} files exist only in the working tree:")
    for line in dirty:
        print(f"  {line}")
    print("\nCommit them before the stage ends. A resumed session reads the")
    print("Migration Directory to decide what is already done, and cannot tell a")
    print("row that was reviewed and committed from one a dead session half-wrote.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
