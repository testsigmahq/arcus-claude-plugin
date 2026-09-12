#!/usr/bin/env python3
"""Check that a block performs every action its source step's code performs.

The fault this exists to catch was measured twice, in the only two scenarios
anyone has reviewed by hand:

    OrderPage.enterQuantity   clear, click, type, click(submitButton)
    the converted block             clear, click, type            <- submit lost

    MenuPage.searchMenu             clear, sendText, pressEnter, click(label)
    the converted block             click, clear, sendText        <- both lost

Both pushed clean. Coverage saw a block present for the step, because presence
is what it asks. The element sweep saw no residue, because the dropped action's
element was never lifted — a drop only leaves a trace when something else
already references what it dropped. Validity and round trip look at the file,
which is self-consistently wrong. Every check the plugin had asks whether what
is in the file is right; none asked whether the file does everything the source
does, and the last action of a sequence is the one that submits it, so losing it
turns a test that acts into a test that fills a form and walks away.

It is deliberately a *heuristic*, and it reports rather than refuses. ADR-0004
keeps source formats in documents rather than parsers, and this stays on the
right side of that line by never parsing: it finds a definition by name, takes
its body by brace matching, and counts calls whose names are actions. That works
the same way in Java, C# or JavaScript, and it is wrong in the same obvious ways
in all three — which is why its output is a question for a reader, not a verdict.

    check_call_chain.py --source-root src --symbol MenuPage.searchMenu <test.sigma> --block "Search menu"

Exit 0 when the block performs at least as many actions as the source, 1 when
the source does something the block does not, and 2 when nothing could be
compared — the symbol did not resolve, or the block was not found. Two is not a
softer one: it means the check did not run, and a caller that treats it as a
failure drowns a real finding in noise.
"""
import argparse
import collections
import functools
import pathlib
import re
import sys

#: Calls whose names mean "change the application's state". Waits, logs and
#: getters are excluded on both sides, because a conversion legitimately
#: reshapes waiting and the comparison has to stay symmetric to mean anything.
#: "check" and "key" are deliberately absent. They matched `checkKey`, a
#: framework helper that performs nothing, and it padded a known-correct row to
#: 5 against 5 — a phantom action hiding a real drop is this check's own fault
#: class reproduced inside it. A narrower vocabulary that misses a checkbox verb
#: is the safer error, because this reports and a reader still reads the names.
SOURCE_ACTIONS = (
    "click", "sendtext", "entertext", "type", "press", "clear",
    "select", "choose", "submit", "upload", "dragand",
    "doubleclick", "rightclick", "hover", "scan", "enter",
)
SIGMA_ACTIONS = (
    "click", "entertext", "clearelementvalue", "press", "select", "upload",
    "doubleclick", "rightclick", "hover", "check", "uncheck", "submit",
    "dragand", "scrollto", "switchto", "storevalue", "navigateto",
)
#: Names that look like actions but are not: a wait built from "clear" or a
#: helper whose name starts with a verb. Kept short and literal on purpose.
NOT_ACTIONS = ("waitfor", "waituntil", "clearcache", "keyword")


#: Comment syntaxes across the languages this walks. Order matters: block
#: comments are stripped before line comments, or a `//` inside a `/* */` ends
#: the wrong thing.
def strip_comments(text):
    """Remove commented-out code before any call is counted.

    A measured run caught this and was right to: a helper had a commented-out
    `click_SubmitUser(...)`, the walk counted it, and the check reported the
    block as missing an action the source does not perform. A false "the source
    does more" is the *inverse* of the fault this exists to catch, and an
    inverse fault is how a check teaches its reader to disregard it — which is
    exactly what happened, except the run cited the document that predicted it
    and overruled the script instead.

    Strings are not protected. A `//` inside a string literal will truncate the
    line, which can only ever *remove* calls from the source side, making the
    check quieter rather than wronger. Protecting them would need a lexer, and
    a lexer is the parser this deliberately does not have.
    """
    out = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)   # C-style block
    out = re.sub(r'"""(?:.|\n)*?"""', " ", out)          # Python docstring
    out = re.sub(r"^\s*#.*$", " ", out, flags=re.M)      # Python / Ruby line
    out = re.sub(r"//.*$", " ", out, flags=re.M)          # C-style line
    return out


def action_calls(body, vocabulary):
    """Every call in `body` whose name reads as an action, in order.

    Commented-out code is removed first; see `strip_comments`.
    """
    body = strip_comments(body)
    found = []
    for name in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
        low = name.lower()
        if any(n in low for n in NOT_ACTIONS):
            continue
        # Prefix, never substring. `elementToBeClickable` contains "click",
        # `getTestType` contains "type" and `containsKey` contains "key"; all
        # three were counted as actions by a first version, which inflated a
        # real finding with three calls that do nothing.
        if low.startswith(vocabulary):
            found.append(name)
    return found


#: Coarse families, so both sides can be compared despite different spellings.
#: Counting alone is not enough: every measured defect was the *tail* of a
#: sequence — a helper's final submit, a scenario's last steps — and a run that
#: drops two tail actions while adding two of its own scores an equal count and
#: passes. Comparing families as a multiset catches the drop whatever was added.
FAMILIES = (
    ("PRESS", ("press", "key")),
    ("TYPE", ("sendtext", "entertext", "type", "scan", "enter")),
    ("CLEAR", ("clear",)),
    ("CLICK", ("click", "doubleclick", "rightclick", "submit", "choose",
               "select", "tap")),
    ("UPLOAD", ("upload",)),
    ("DRAG", ("dragand",)),
    ("HOVER", ("hover",)),
)


def family(name):
    low = name.lower()
    for label, prefixes in FAMILIES:
        if low.startswith(prefixes):
            return label
    return "OTHER"


@functools.lru_cache(maxsize=8)
def source_files(root):
    """Every file the walk may look in, listed once.

    Listing the tree at every node made a two-level walk over a few hundred
    files take minutes; with the cycle guard widened it stopped finishing at
    all. The walk is called once per block and recurses, so the tree is listed
    hundreds of times for an answer that never changes.
    """
    return tuple(p for p in pathlib.Path(root).rglob("*")
                 if p.is_file() and p.suffix in
                 (".java", ".cs", ".js", ".ts", ".py", ".rb"))


@functools.lru_cache(maxsize=4096)
def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


#: A signature whose return type is not `void` — a getter. `By getByFromPage(...)`
#: returns a locator; it does not perform the step. Recursing into it found a
#: `click` in something it called and reported three correct verify blocks as
#: missing an action nothing performs.
RETURNS_VALUE = "returns-value"


@functools.lru_cache(maxsize=65536)
def returns_value(text, name):
    """Whether `name`'s definition declares a non-void return type.

    Only meaningful where a language writes return types. Where it does not —
    Python, JavaScript, Ruby — this answers False and the walk recurses as
    before, which is the safe direction: a missed skip adds noise a reader can
    see, a wrong skip hides an action.
    """
    m = re.search(r"\b(?:public|private|protected|static|final|\s)*"
                  r"([A-Za-z_][A-Za-z0-9_<>\[\].]*)\s+"
                  + re.escape(name) + r"\s*\(", text)
    if not m:
        return False
    kind = m.group(1)
    return kind not in ("void", "def", "function", "public", "private",
                        "protected", "static", "final")


@functools.lru_cache(maxsize=65536)
def definition_body(text, name):
    """The body of `name`'s definition, by brace matching. None if absent.

    Brace matching rather than parsing: the point is to bound a region, and a
    parser would be the first one in the plugin.
    """
    m = re.search(r"\b" + re.escape(name) + r"\s*\([^)]*\)\s*\{", text)
    if not m:
        return None
    start = text.index("{", m.end() - 1)
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    return None


def walk(root, symbol, depth, seen=None, depth_is_top=True, near=None):
    """Action calls reached from `symbol`, following calls `depth` levels down.

    A step definition rarely acts itself; it calls a page object that does. One
    level would therefore find nothing at all, and unlimited depth walks into
    the framework's own plumbing, where every helper clicks something.
    """
    seen = seen if seen is not None else set()
    name = symbol.split(".")[-1]
    if depth < 0:
        return []
    # When the symbol names a class, prefer a file that declares it. Matching on
    # the method name alone let `NoSuchClass.searchMenu` resolve to the real
    # `searchMenu` elsewhere and report a confident result for a symbol that
    # does not exist — a check answering a question it was not asked.
    owner = symbol.split(".")[0] if "." in symbol else None
    candidates = list(source_files(root))
    if owner:
        preferred = [p for p in candidates if p.stem == owner]
        if preferred:
            candidates = preferred
        elif depth_is_top:
            # Not an error — a file name is not a class name in every language —
            # but it must be visible, or a typo'd owner resolves to a same-named
            # method elsewhere and the result looks confident.
            print(f"note: no file under the source root is named {owner!r}; "
                  f"matching on {name!r} alone")
    elif near is not None:
        # A callee is nearly always defined beside its caller, and the same
        # method name often exists in several page objects with different
        # bodies. Resolving `searchMenu` globally picked a namesake carrying an
        # extra keypress and reported a correct block as missing an action —
        # the inverse fault again, from ambiguity rather than from comments.
        candidates = [near] + [c for c in candidates if c != near]
    for path in candidates:
        body = definition_body(read(path), name)
        if body is None:
            continue
        # The cycle guard keys on file *and* name. Keying on the name alone
        # meant a step definition delegating to an identically named page
        # method — `WMS_Web.navigateToItemsPage` calling
        # `HomePage.navigateToItemsPage` — was blocked by its own entry, so the
        # walk reported zero actions and the block went unchecked. That naming
        # is the common case in this kind of suite, not an edge.
        key = (path, name)
        if key in seen:
            continue
        seen.add(key)
        actions = action_calls(body, SOURCE_ACTIONS)
        if depth:
            for callee in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
                if callee.lower().startswith(SOURCE_ACTIONS):
                    continue
                if any(returns_value(read(c), callee) for c in candidates
                       if definition_body(read(c), callee) is not None):
                    # A getter's job is to return something, not to act.
                    continue
                actions += walk(root, callee, depth - 1, seen,
                                depth_is_top=False, near=path)
        return actions
    return []


def block_body(sigma_text, label_fragment):
    """The body of the first block whose label contains `label_fragment`."""
    for m in re.finditer(r'^\s*block\s+"((?:[^"\\]|\\.)*)"[^{]*\{', sigma_text, re.M):
        if label_fragment.lower() not in m.group(1).lower():
            continue
        start = sigma_text.index("{", m.end() - 1)
        depth = 0
        for i in range(start, len(sigma_text)):
            if sigma_text[i] == "{":
                depth += 1
            elif sigma_text[i] == "}":
                depth -= 1
                if depth == 0:
                    return m.group(1), sigma_text[start + 1:i]
    return None, None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", required=True)
    p.add_argument("--symbol", required=True,
                   help="the source method the row was derived from, e.g. MenuPage.searchMenu")
    p.add_argument("--block", required=True, help="a fragment of the block's label")
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("test")
    args = p.parse_args()

    source = walk(args.source_root, args.symbol, args.depth)
    text = pathlib.Path(args.test).read_text(encoding="utf-8")
    label, body = block_body(text, args.block)
    if body is None:
        print(f"no block's label contains {args.block!r}")
        return 2
    converted = action_calls(body, SIGMA_ACTIONS)

    print(f"block:  {label}")
    print(f"source: {len(source)} actions  {' '.join(source)}")
    print(f"block:  {len(converted)} actions  {' '.join(converted)}")

    if not source:
        print(f"\n{args.symbol} was not found under {args.source_root}, or performs no")
        print("action. Nothing was compared, and that is not a pass — check the symbol.")
        return 2

    missing = collections.Counter(family(a) for a in source)
    missing.subtract(collections.Counter(family(a) for a in converted))
    missing = {k: v for k, v in missing.items() if v > 0 and k != "OTHER"}

    if len(converted) < len(source) or missing:
        if missing:
            shortfall = ", ".join(f"{v}x {k}" for k, v in sorted(missing.items()))
            print(f"\nThe source performs actions the block does not: {shortfall}")
        else:
            print(f"\nThe source performs {len(source) - len(converted)} more actions than the block.")
        print("The last action of a sequence is usually the one that submits it, so")
        print("check the end of the chain first. Either convert what is missing, or")
        print("record it as a Concession on the row and name it in the block's label.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
