#!/usr/bin/env python3
"""Stop hook: refuse to end a session that leaves a Migration uncommitted.

Every rule this plugin turned into a check held. Every rule that stayed prose
was followed in one run and skipped in the next, and the sharpest case was a
gate that *ran*: one run executed `check_committed.py` twice, was told 15 files
existed only in the working tree, staged them, and ended without committing.
Running a check and acting on it are different things, and nothing in a
document closes that gap — the document is what was already being skipped.

So this is not another instruction. A Stop hook is the one place the plugin can
make a verdict consequential: the session does not end while the Migration's
own record is unsaved.

Silence is the default. If there is no Migration under the working directory
this exits 0 and says nothing, because the plugin is installed in sessions that
have nothing to do with a migration and a hook that talks in those is a hook
people disable.
"""
import json
import os
import pathlib
import subprocess
import sys

WATCHED = (".testsigma/migration", "tests/testsigma")


def migration_root(start):
    """The nearest directory at or above `start` holding a Migration."""
    here = pathlib.Path(start).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".testsigma" / "migration").is_dir():
            return candidate
        for child in candidate.iterdir() if candidate.is_dir() else ():
            try:
                if child.is_dir() and (child / ".testsigma" / "migration").is_dir():
                    return child
            except OSError:
                continue
        if candidate == here.parents[-1] if here.parents else False:
            break
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    # Never loop: if this hook already blocked once and the model is still
    # stopping, saying it again would trap the session.
    if payload.get("stop_hook_active"):
        return 0

    start = payload.get("cwd") or os.getcwd()
    try:
        root = migration_root(start)
    except OSError:
        return 0
    if root is None:
        return 0

    try:
        out = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                             capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return 0

    dirty = [l.rstrip() for l in out.splitlines()
             if any(w in l[3:] for w in WATCHED)]
    if not dirty:
        return 0

    listing = "\n".join(f"  {l}" for l in dirty[:20])
    more = f"\n  ... and {len(dirty) - 20} more" if len(dirty) > 20 else ""
    print(json.dumps({
        "decision": "block",
        "reason": (
            f"{len(dirty)} files under the Migration exist only in the working "
            f"tree:\n{listing}{more}\n\n"
            "Staging is not committing. A resumed session reads the Migration "
            "Directory to decide what is already done, and git history is the "
            "only thing that separates a row someone reviewed from one a dead "
            "session half-wrote. Commit them, scoped to the Migration "
            "Directory and the working copy, then finish."
        ),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
