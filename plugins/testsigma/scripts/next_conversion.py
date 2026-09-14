#!/usr/bin/env python3
"""Choose the scenario to convert next, by greedy set cover.

A Migration delivers one Conversion at a time (ADR-0012), and the order matters
while vocabulary is still being learned: the scenario that introduces the most
Source Steps nobody has judged yet front-loads the judgement while it is still
cheap to correct, and makes every Conversion after it cheaper faster.

This is a script rather than a paragraph in a skill because it is exact by
construction, in the same sense survey's enumeration is. Left as prose, two
sessions reading the same Migration Directory choose differently and neither is
wrong, which is precisely the state that makes a queue unreadable.

    next_conversion.py --suite <suite root>

It reads `scenarios.md` for the queue and the incidence and `step-map.md` for
what has been judged. **The unseen count is computed here, every time, and never
read from a stored column** — a stored count is stale the moment any Conversion
finishes, and a stale count does not announce itself: it silently mis-orders the
queue.

Exit 0 when a scenario is selected, 1 when there is nothing to select or the
files it needs are missing. Absence is never a pass here either: no selection is
a thing to report, not a thing to infer from silence.
"""
import argparse
import pathlib
import re
import sys

#: Below this many unseen Source Steps, vocabulary has saturated and ordering
#: hands over to the Operator's priority. It is a property of the curve rather
#: than a count of Conversions: one suite flattens at the eighth and another at
#: the fortieth, so counting Conversions would guess at a suite's shape.
DEFAULT_THRESHOLD = 3

#: A row is decided when someone has ruled on it, whichever way they ruled.
#: `unreviewed` is the only status that still costs the judgement this ordering
#: exists to front-load: `residue` was judged inexpressible, `adopted` judged
#: already expressed, and neither is re-read by the Conversion that meets it.
DECIDED = {"reviewed", "adopted", "residue"}

SELECTABLE = "pending"


def table(text):
    """Rows of the first markdown table, as dicts keyed by header cell.

    Markdown rather than a data format because a person reviews these files in
    the source repository's diffs — the same reason the Migration Directory is
    one file per concern rather than one state file.
    """
    header, rows = None, []
    for line in text.split("\n"):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if header is None:
            header = cells
            continue
        rows.append(dict(zip(header, cells + [""] * (len(header) - len(cells)))))
    return rows


def steps(cell):
    """The Source Steps one incidence cell names.

    Backticks delimit, because a Source Step's own text may hold a comma —
    `I enter "a, b" in the field` is one step, and splitting on commas alone
    would score it as two and over-count what the scenario introduces.
    """
    quoted = re.findall(r"`([^`]+)`", cell)
    if quoted:
        return [s.strip() for s in quoted if s.strip()]
    return [s.strip() for s in cell.split(",") if s.strip()]


def decided_steps(step_map_text):
    """The Source Steps the Step Map has already ruled on."""
    out = set()
    for row in table(step_map_text):
        step = row.get("Source Step", "").strip().strip("`")
        if step and row.get("Status", "").strip().lower() in DECIDED:
            out.add(step)
    return out


def unseen(scenario_row, decided):
    """How many Source Steps this scenario would be the first to judge.

    Distinct within the scenario: a step written twice is judged once, so
    counting occurrences would rank a repetitive scenario above one that
    actually teaches the Migration more.
    """
    return len({s for s in steps(scenario_row.get("Source Steps reached", ""))
                if s not in decided})


def choose(scenarios, decided):
    """The next Conversion, or None. Deterministic, including at a tie.

    A tie is broken by scenario name, which is arbitrary and that is the point:
    two sessions reading the same Migration Directory must select the same
    scenario, or the queue means something different to each of them. File order
    would not do — a row moved by an unrelated edit would change the choice.
    """
    candidates = [
        (unseen(row, decided), row.get("Scenario", "").strip().strip("`"))
        for row in scenarios
        if row.get("Status", "").strip().lower() == SELECTABLE
    ]
    if not candidates:
        return None
    # Most unseen first, then by name. Sorting rather than max() so the tie
    # break is the visible half of the rule rather than an inverted key.
    return sorted(candidates, key=lambda c: (-c[0], c[1]))[0]


def counts(scenarios):
    tally = {}
    for row in scenarios:
        status = row.get("Status", "").strip().lower() or "(no status)"
        tally[status] = tally.get(status, 0) + 1
    return tally


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", required=True, help="the source suite's root")
    p.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                   help="hand over to Operator priority below this many unseen")
    args = p.parse_args()

    migration = pathlib.Path(args.suite) / ".testsigma" / "migration"
    scenarios_file = migration / "scenarios.md"
    step_map_file = migration / "step-map.md"
    for path in (scenarios_file, step_map_file):
        if not path.exists():
            print(f"no {path.name} at {path}. The queue and what has been judged")
            print("both live in the Migration Directory, and without them there is")
            print("no ordering to compute — which is not the same as no work left.")
            return 1

    scenarios = table(scenarios_file.read_text(encoding="utf-8"))
    decided = decided_steps(step_map_file.read_text(encoding="utf-8"))
    tally = counts(scenarios)

    print(f"scenarios:    {len(scenarios)} total, " + ", ".join(
        f"{n} {status}" for status, n in sorted(tally.items())))
    print(f"judged:       {len(decided)} Source Steps")

    chosen = choose(scenarios, decided)
    if chosen is None:
        print("\nNo scenario is pending. Everything is delivered, parked or out of")
        print("scope, so there is no next Conversion to take. A parked one is taken")
        print("up again by answering what it waits on, not by this ordering.")
        return 1

    introduces, scenario = chosen
    print(f"next:         {scenario}")
    print(f"introduces:   {introduces} unseen Source Steps")

    if introduces < args.threshold:
        print("\nVocabulary has saturated: the best remaining scenario introduces")
        print(f"fewer than {args.threshold} Source Steps nobody has judged, so no")
        print("order left teaches the Migration much more than any other. Ordering")
        print("hands over to the Operator's priority from here — tell them, and ask")
        print("which scenarios the customer wants first. The scenario named above")
        print("is a default, not a recommendation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
