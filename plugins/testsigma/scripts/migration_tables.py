#!/usr/bin/env python3
"""Reading the Migration Directory's tables.

Markdown rather than a data format because a person reviews these files in the
source repository's diffs — the same reason the directory is one file per
concern rather than one state file. That choice puts a small amount of parsing
in every script that reads them, and this is the one copy of it.

Nothing here decides anything. The rules live in the scripts that import it, so
that a change to a rule is visible in the file named for it.
"""
import re


def split_cells(line):
    """One table line's cells, trimmed. Not a table row unless it starts `|`."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_divider(cells):
    """The `|---|---|` line under a header, which carries no data."""
    return all(set(c) <= set("-: ") for c in cells)


def table(text):
    """Rows of the file's table, as dicts keyed by the first header row's cells.

    Every pipe line in the file is read, and the first is taken as the header.
    These files hold one table each by construction — `migration-directory.md`
    fixes the shape of every one of them — so a second table would be a file
    something else had already broken.

    A short row is padded rather than rejected: a trailing empty cell is
    routinely dropped by an editor, and a `Reason` nobody filled in is a fact
    about the row, not a malformed file.
    """
    header, rows = None, []
    for line in text.split("\n"):
        if not line.strip().startswith("|"):
            continue
        cells = split_cells(line)
        if is_divider(cells):
            continue
        if header is None:
            header = cells
            continue
        rows.append(dict(zip(header, cells + [""] * (len(header) - len(cells)))))
    return rows


def items(cell):
    """The backtick-delimited items one cell names.

    Backticks delimit, because a Source Step's own text may hold a comma —
    `I enter "a, b" in the field` is one step, and splitting on commas alone
    would score it as two. Where a cell carries no backticks at all, commas are
    the fallback, so a hand-written row is still read.
    """
    quoted = re.findall(r"`([^`]+)`", cell)
    if quoted:
        return [s.strip() for s in quoted if s.strip()]
    return [s.strip() for s in cell.split(",") if s.strip()]


def read(migration, *names):
    """The named files' text, or the name of the first one missing.

    Returns (texts, missing). Absence is never a pass: a script that cannot see
    the queue has nothing to say about it, which is not the same as having
    nothing to do.
    """
    texts = []
    for name in names:
        path = migration / name
        if not path.exists():
            return None, name
        texts.append(path.read_text(encoding="utf-8"))
    return texts, None
