#!/usr/bin/env python3
"""Check a test's `param` references against the profile it declares.

`validate` checks that a `param` name exists *somewhere in the workspace* — it
pools every profile's columns into one set. So a test bound to one profile may
reference another profile's column and compile cleanly:

    param.notInAnyProfile   TSF2021 refused
    param.onlyInB           accepted, from a test bound to ProfileA

At run time the value comes from the profile actually in scope, which has no
such column, and the run **fails**: `ParameterTestDataProcessor` ends in
`validateTestDataNotFound`, which throws "test data not found". Both spellings
reach it — a whole-slot `param` and an `@|param|` inside text.

That certainty is the reason to run this, and it is the opposite of the reason
an earlier version of this file gave. A cross-profile reference is not something
that might work; it is a run that will definitely fail, found offline in a second
rather than in a pipeline. There is no "might be fine" case to soften it with.

Only one of the three reference kinds is silent, and it is not this one:

    param missing    → run fails, "test data not found"
    env missing      → run fails
    runtime missing  → the marker survives as literal text, the step passes

So the silent-pass class belongs to **runtime variables**. This check does not
cover it.

Deliberately not covered, each because checking it would report faults that are
not faults:

* A test declaring no profile. Unbound `param` is the norm rather than an edge
  case — the profile arrives from a suite or plan at run time — and refusing it
  would flag most of a healthy workspace, which is how a check gets switched off.

* A step group's body. The reason is the **caller**: resolution walks to the
  step-group step in the calling test and on to the root test's profile, so a
  group's own profile is not the scope its references resolve in. A group read
  on its own settles nothing about what its parameters mean.

* A reference inside an enclosing `for … in tdp["Other"]`. The loop's profile
  beats the test's own, so such a reference resolves against `Other`. Verified:
  a test bound to ProfA looping `tdp["ProfB"].rows()` and reading `param.inB` is
  correct, and the first version of this script flagged it.

* The target of `override(param.x, …)` at a group call site, which replaces the
  value there rather than resolving it.

    check_profile_refs.py <workspace root>

Exit 0 when every bound test's references resolve in its own profile.
"""
import pathlib
import re
import sys

PROFILE = re.compile(r'profile\s*=\s*tdp\["([^"]+)"\]')
TDP_NAME = re.compile(r'^\s*tdp\s+"([^"]+)"', re.M)
COLUMN = re.compile(r'column\("([^"]+)"\)')
REF_BRACKET = re.compile(r'param\["([^"]+)"\]')
REF_DOT = re.compile(r"param\.([A-Za-z_][A-Za-z0-9_]*)")


FOR_OVER_TDP = re.compile(r'^\s*for\s+\w+\s+in\s+tdp\["([^"]+)"\]')
GROUP_OPEN = re.compile(r'^\s*group\s+"')
OVERRIDE = re.compile(r"override\(\s*param\.[A-Za-z_][A-Za-z0-9_]*")


def unresolved(text, declared, profiles):
    """Names that resolve in no profile actually in scope at that line.

    Scope is not "the test's profile". Resolution walks five levels and an
    enclosing loop's profile beats the test's own, so this carries a stack of
    (profile, depth-at-which-it-opened): a `for … in tdp["Other"]` pushes
    `Other`, and the entry pops when the brace depth returns to where it opened.

    Popping on depth rather than on a brace count is what makes the scope *end*.
    A first attempt pushed correctly and never popped, so a genuine fault after
    the loop's closing brace went unreported — a check that stops checking
    part-way through a file, which is worse than one that never ran.

    A `group` call's body is skipped: the caller supplies its data, so a group
    read alone settles nothing. `override(param.x, …)` targets are dropped for
    the same reason — the name there is replaced, not resolved.
    """
    scopes = [(declared, 0)]
    skip_depth = None
    depth = 0
    out = set()
    for line in text.split("\n"):
        opens = line.count("{") - line.count("}")

        if skip_depth is None and GROUP_OPEN.search(line):
            skip_depth = depth
            depth += opens
            continue

        if skip_depth is None:
            loop = FOR_OVER_TDP.search(line)
            if loop:
                scopes.append((loop.group(1), depth))
            else:
                # The levels are a fallback chain, not a single scope: an
                # enclosing loop's profile is tried first and resolution falls
                # through to the test's own when it misses. Checking only the
                # innermost flagged `param.inA` inside a loop over another
                # profile — correct code, reported as a fault, which is the
                # second false positive this walker produced before it was
                # checked against one.
                in_scope = set()
                for scope, _ in scopes:
                    in_scope |= profiles.get(scope, set())
                names = set(REF_BRACKET.findall(line)) | set(
                    REF_DOT.findall(OVERRIDE.sub("", line))
                )
                out |= names - in_scope

        depth += opens

        if skip_depth is not None and depth <= skip_depth:
            skip_depth = None
        while len(scopes) > 1 and depth <= scopes[-1][1]:
            scopes.pop()
    return out


def read(path):
    return path.read_text(encoding="utf-8", newline="")


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")

    profiles = {}
    for f in root.rglob("*.tdp.sigma"):
        text = read(f)
        name = TDP_NAME.search(text)
        if name:
            profiles[name.group(1)] = set(COLUMN.findall(text))

    checked = skipped = 0
    faults = []
    for f in sorted(root.rglob("*.test.sigma")):
        text = read(f)
        bound = PROFILE.search(text)
        if not bound:
            skipped += 1
            continue
        checked += 1
        name = bound.group(1)
        if name not in profiles:
            faults.append((f, name, ["<profile not in this workspace>"]))
            continue
        missing = sorted(unresolved(text, name, profiles))
        if missing:
            faults.append((f, name, missing))

    print(f"tests checked: {checked}   skipped (no profile declared): {skipped}")
    for f, name, missing in faults:
        print(f"\n{f}")
        print(f"  binds profile `{name}`, and references columns it does not have:")
        for m in missing:
            print(f"    {m}")
    if faults:
        print("\n`validate` accepts these: it checks the workspace, not the profile.")
        print("At run time the lookup throws — \"test data not found\" — so each of")
        print("these is a run that will definitely fail, found here instead of there.")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
