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

    check_committed.py --suite <suite root>

Exit 0 when the tree is clean, 1 when it is not.
"""
import argparse
import pathlib
import subprocess
import sys

WATCHED = (".testsigma/migration", "tests/testsigma")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", default=".")
    args = p.parse_args()
    root = pathlib.Path(args.suite).resolve()

    try:
        out = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"cannot read git status under {root}: {e}")
        print("The Migration's state lives in git history; without it a resumed")
        print("session cannot tell reviewed work from a half-written session.")
        return 1

    dirty = []
    for line in out.splitlines():
        path = line[3:].strip().strip('"')
        if any(w in path for w in WATCHED):
            dirty.append(line.rstrip())

    if not dirty:
        print("nothing uncommitted under the Migration Directory or the working copy.")
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
