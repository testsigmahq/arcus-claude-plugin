#!/usr/bin/env python3
"""Check that an assembled test accounts for every step of its source scenario.

The fault this exists to catch was measured, and it is the worst shape a
conversion can take. A run converted the nine API steps at the head of a
fifty-five step scenario, stopped, and reported "all 7 steps (pure API, no UI)".
The file compiled. The tenant accepted it. `pull` reported no difference. The
Residue table was empty, so nothing anywhere recorded that forty-six steps were
missing, and every signal the Migration produces said the work was done.

No existing check could see it. Validity looks at what is in the file. The order
check looks at how what is in the file is arranged. The element sweep finds a
dropped step only when it left an element behind, and these were dropped before
any element was lifted. Every check the plugin had asks whether the file is
right; none asked whether it is *all there*.

So the arithmetic is a comparison against the source, and it needs the source's
steps. It does not read them itself: ADR-0004 keeps source formats in documents
rather than parsers, and a Gherkin reader here would be the first parser. The
caller supplies the steps it already read while mapping, one per line, and this
compares them against the test's block labels.

    check_coverage.py --steps steps.txt <test.sigma>

Exit 0 when every source step is accounted for, 1 otherwise.
"""
import argparse
import collections
import pathlib
import re
import sys

KEYWORD = re.compile(r"^(?:Given|When|Then|And|But)\s+", re.I)
BLOCK = re.compile(r'^\s*block\s+"((?:[^"\\]|\\.)*)"')


def normalise(text):
    """A step's identity: keyword dropped, whitespace collapsed, lowered.

    The keyword is not part of what a step means — a scenario writes `And Search
    ASN` where a later one writes `When Search ASN`, and they are one step. The
    same normalisation runs over both sides so the comparison is symmetric.
    """
    text = KEYWORD.sub("", text.strip())
    return " ".join(text.split()).lower()


def labels(sigma_text):
    """Block labels that *claim* a source step, unescaped, in document order.

    Returns `(claims, nested)`. A block written inside another block is not a
    second claim, and it is not legal either: the tenant has no nested blocks,
    so a block holds steps and a block is not a step. It is returned separately
    so the caller can report it rather than silently absorb it.

    The shape it replaces was a marker tucked inside the step it qualified:

        block "Validate list of UI values …"        <- claims the source step
            block "Needs a step addon: check all 10 values …"   <- refused

    That read well, and the wire rejects it. The need now rides in the claiming
    block's own label as a parenthesised suffix, which the matching below
    already tolerates, so a gap costs no coverage and no nesting.

    Depth is still not the rule: a step's own block may sit inside an `if` or a
    `while`, and only counting top-level blocks would call a correctly nested
    conversion incomplete. The rule is about *claiming parents* — a block under
    `if` claims, a block under a block does not.
    """
    found = []
    nested = []
    claiming_depth = None
    depth = 0
    for line in sigma_text.split("\n"):
        m = BLOCK.search(line)
        if m:
            label = m.group(1).replace('\\"', '"').replace("\\\\", "\\")
            label = re.sub(r"^Step:\s*", "", label)
            if claiming_depth is None:
                found.append(label)
                claiming_depth = depth
            else:
                nested.append(label)
        depth += line.count("{") - line.count("}")
        if claiming_depth is not None and depth <= claiming_depth:
            claiming_depth = None
    return found, nested


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", required=True,
                        help="the source scenario's steps, one per line")
    parser.add_argument("test", help="the assembled .sigma test")
    args = parser.parse_args()

    steps = [s for s in pathlib.Path(args.steps).read_text(
        encoding="utf-8").split("\n") if s.strip()]
    text = pathlib.Path(args.test).read_text(encoding="utf-8", newline="")
    found, nested = labels(text)

    # Coverage is a multiset, not a set. A scenario may write the same step
    # twice — `Click on Row At First Index` appears twice in the measured one —
    # and set membership says both are covered when only one block exists. A
    # first version scored exactly that as "4 of 4" while reporting "blocks: 3"
    # two lines above, which is the shape of failure this whole check exists to
    # refuse, reproduced inside it.
    #
    # A label may also carry a disambiguating suffix, which is good authoring:
    # two identical steps in one scenario read better as `… (PIX Visibility)`.
    # So a block claims a step when its label equals the step or begins with it
    # followed by a bracketed qualifier — nothing looser, or an unrelated block
    # whose label happens to share a prefix would absorb a step it never did.
    remaining = collections.Counter(normalise(s) for s in steps)
    extra = []
    for label in found:
        key = normalise(label)
        base = re.sub(r"\s*\([^()]*\)$", "", key).strip()
        for candidate in (key, base):
            if remaining.get(candidate):
                remaining[candidate] -= 1
                break
        else:
            extra.append(label)
    missing = []
    for step in steps:
        key = normalise(step)
        if remaining.get(key):
            remaining[key] -= 1
            missing.append(step)

    print(f"source steps: {len(steps)}")
    print(f"blocks:       {len(found)}")
    print(f"accounted:    {len(steps) - len(missing)} of {len(steps)}")

    if not found and steps:
        # The measured failure had zero labelled blocks: the test was written as
        # bare statements, so there was nothing to compare and nothing noticed.
        print("\nNo block carries a source step's text. A converted scenario is")
        print("assembled one block per source step, labelled with that step, so")
        print("that what is present can be compared with what should be. Without")
        print("the envelope this check cannot run, and its silence is not a pass.")
        return 1

    if missing:
        print(f"\n{len(missing)} source steps are accounted for by nothing:")
        for s in missing:
            print(f"  {s}")
        print("\nEach one is converted, or stands as an empty block naming what")
        print("was needed. Absent from the file, it is absent from the test, and")
        print("the test reads as a complete conversion of its source.")
    if extra:
        print(f"\n{len(extra)} blocks match no source step:")
        for l in extra:
            print(f"  {l}")
    if nested:
        print(f"\n{len(nested)} blocks are written inside another block:")
        for l in nested:
            print(f"  {l}")
        print("\nA block holds steps, and a block is not a step, so the tenant")
        print("refuses this. Where the inner block named work that was needed,")
        print("put that need in the outer block's label as a parenthesised")
        print("suffix after the source step's text, and leave the body to hold")
        print("whatever did convert.")

    return 1 if missing or extra or nested else 0


if __name__ == "__main__":
    sys.exit(main())
