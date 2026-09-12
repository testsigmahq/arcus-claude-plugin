#!/usr/bin/env python3
"""Check a test's `param` references against the profile it declares.

`validate` checks that a `param` name exists *somewhere in the workspace* — it
pools every profile's columns into one set. So a test bound to one profile may
reference another profile's column and compile cleanly:

    param.notInAnyProfile   TSF2021 refused
    param.onlyInB           accepted, from a test bound to ProfileA

At run time the value comes from the bound profile, which has no such column.
Nothing substitutes, the step reads literal marker text, and it still passes.
That is a test that runs green and checks nothing — the same silent-pass class
as a locator with an unresolvable parameter, but reachable from any ordinary
data-driven test rather than from a handful of dynamic elements.

This closes the gap for the common case and deliberately not for all of them:

* A test declaring no profile is skipped. Unbound `param` is the norm rather
  than an edge case — the profile arrives from a suite or plan at run time —
  and refusing it would flag most of a healthy workspace.
* Only the declaring test's own profile is consulted. Step-group profiles and
  `override(param.x, …)` need establishing before they can be checked, and a
  rule applied past where it has been established is how the thing it is
  checking got into the build.

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
        refs = set(REF_BRACKET.findall(text)) | set(REF_DOT.findall(text))
        missing = sorted(refs - profiles[name])
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
        print("At run time nothing substitutes, the step reads the marker as text,")
        print("and the test passes having checked nothing.")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
