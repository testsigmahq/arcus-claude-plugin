#!/usr/bin/env python3
"""Run the call-chain comparison for every block in an assembled test.

`check_call_chain.py` takes one symbol and one block, so using it well means
remembering to use it — and a measured run did not. The rule that a row reused
by a new scenario gets re-checked was written into the mapping stage, and the
next run performed zero call-chain checks. The run before it ran one, on a
single representative row, chosen by judgement.

A rule that depends on remembering which rows deserve attention is a rule that
samples. This takes the judgement out: every block in the test is matched to
its Step Map row, and every row carrying a `Source` symbol is checked. Reused
rows are covered because they are in the test, not because anyone classified
them as reused.

    check_stage.py --suite <suite> --source-root <src> <test.sigma>

Exit 0 when every checked block performs at least as many actions as its
source, 1 otherwise.
"""
import argparse
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
BLOCK = re.compile(r'^\s*block\s+"((?:[^"\\]|\\.)*)"', re.M)
#: A label whose parenthesised suffix declares the gap — see authoring.md.
DECLARED = re.compile(r"\((?:needs|no-op|blocked|no step)\b", re.I)


def rows(step_map_text):
    """(source-step text, Source symbol) for rows carrying provenance."""
    out = []
    for line in step_map_text.split("\n"):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].startswith("---") or cells[0] == "Source Step":
            continue
        step, source = cells[0].strip("`"), cells[2]
        if source and not source.startswith("---"):
            out.append((step, source))
    return out


def pattern(step):
    """A regex matching a block label produced from this Source Step.

    Survey normalises literal arguments into `<param>`, and assembly writes the
    occurrence's real value back in, so the row and the label differ exactly
    where the parameters are.
    """
    parts = [re.escape(p) for p in re.split(r'""?<param>""?|<param>|<number>', step)]
    return re.compile(".*".join(parts), re.I)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", required=True)
    p.add_argument("--source-root", required=True)
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("test")
    args = p.parse_args()

    suite = pathlib.Path(args.suite)
    step_map = suite / ".testsigma" / "migration" / "step-map.md"
    if not step_map.exists():
        print(f"no Step Map at {step_map} — nothing to check against, which is")
        print("not a pass: the provenance this needs lives there.")
        return 1

    known = rows(step_map.read_text(encoding="utf-8"))
    labels = [m.group(1) for m in BLOCK.finditer(
        pathlib.Path(args.test).read_text(encoding="utf-8"))]

    checked, failed, unresolved, declared, unprovenanced = 0, [], [], [], 0
    for label in labels:
        plain = label.replace('\\"', '"')
        match = next((s for step, s in known if pattern(step).search(plain)), None)
        if match is None:
            unprovenanced += 1
            continue
        # A row may name a chain; the first symbol is the entry point and the
        # walk finds the rest itself.
        symbol = re.split(r"[/,]| \(", match)[0].strip()
        r = subprocess.run(
            [sys.executable, str(HERE / "check_call_chain.py"),
             "--source-root", args.source_root, "--symbol", symbol,
             # The raw label, not the unescaped one: block bodies are found by
             # substring against the label as written, and a label holding
             # `\"` stops matching the moment the quotes are unescaped. That
             # alone accounted for most of the blocks this could not compare.
             "--block", label[:60], "--depth", str(args.depth), args.test],
            capture_output=True, text=True)
        if r.returncode not in (0, 1, 2) or "Traceback" in r.stderr:
            # A crashing child exits 1, which is indistinguishable from "the
            # block is short" unless this looks. A first version reported all
            # 41 blocks as failing because the child had a syntax error.
            unresolved.append((label, f"{symbol} — the check itself failed"))
            continue
        if r.returncode == 2:
            # The symbol did not resolve. Not a finding about the block, and
            # counting it as one turned 5 real candidates into 36 "failures"
            # in the first version of this script — the noise that makes a
            # check ignorable, built into the thing meant to stop that.
            unresolved.append((label, symbol))
            continue
        checked += 1
        if r.returncode == 1:
            if DECLARED.search(plain):
                # The label already says this block does less than its source
                # and why. That is the marker convention working, not a drop —
                # reporting it as a fault would train a reader to ignore the
                # one check that finds real ones.
                declared.append(label)
            else:
                failed.append((label, symbol, r.stdout.strip()))

    print(f"blocks:        {len(labels)}")
    print(f"compared:      {checked}")
    print(f"unresolved:    {len(unresolved)}")
    print(f"declared gaps: {len(declared)}")
    print(f"no provenance: {unprovenanced}")

    if failed:
        print(f"\n{len(failed)} blocks perform fewer actions than their source:\n")
        for label, symbol, out in failed:
            print(f"  {label[:90]}")
            print(f"    via {symbol}")
            for line in out.split("\n"):
                if line.startswith(("source:", "block:", "note:")):
                    print(f"    {line}")
            print()
    if unresolved:
        print(f"{len(unresolved)} blocks could not be compared — the row's Source")
        print("symbol did not resolve to a definition performing any action:")
        for label, symbol in unresolved[:12]:
            print(f"  {label[:70]}  via {symbol}")
        if len(unresolved) > 12:
            print(f"  ... and {len(unresolved) - 12} more")
        print("These are not passes. Usually the row names a wrapper that only")
        print("delegates, or names the chain in prose the first-symbol split")
        print("cannot read — fix the row's Source, not the test.")
    if unprovenanced:
        print(f"\n{unprovenanced} blocks matched no Step Map row carrying a Source")
        print("symbol. They were not checked, and not-checked is not passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
