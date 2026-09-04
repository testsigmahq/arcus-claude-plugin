#!/usr/bin/env python3
"""Check document order and block nesting in a `.sigma` test.

The fault this exists to catch is the one a person found by looking at the
application: a conditional whose body is numbered outside its own block, so the
block draws empty and its steps run after everything else. A test carrying it
compiles, is accepted by the tenant, and survives a round trip, because the
round trip rebuilds the step tree from parentage and so cannot see order.

The property is arithmetic. For every step with a parent:

    order(parent) < order(step) < order(parent's next sibling)

with no upper bound where the parent has no next sibling. Siblings must also
increase in document order. The plugin computes this itself rather than asking
the CLI, so the check holds whatever the installed build happens to verify —
which is the concrete case behind ADR-0003.

**The order value is not the `[id = N]`.** An id is an identity assigned when a
step is created, so a step inserted later carries a higher id while sitting
earlier in the document — measured on a real conversion, a top-level step at
1718 precedes one at 1604. Reading ids as order reports faults that are only
authoring history.

So a `.sigma` working copy cannot carry this fault: its parentage and document
order are the lexical nesting and the lexical sequence, both correct by
construction. The fault appears in the order numbers the platform assigns, which
is why it reached a tenant and survived a round trip.

This script therefore does two separable things. Given a working copy it derives
the correct order — the pre-order walk of the lexical tree — which is the
authority the plugin computes for itself. Given order numbers reported by the
platform, it checks them against the property and names every step out of place.

Usage:
    check_step_order.py <file.sigma> ...                 print the correct order
    check_step_order.py <file.sigma> --orders <json>     check reported orders

The JSON is an object mapping step id to the order number the platform reports.
Exit status is 0 when every file is clean and 1 when any step is out of place.
"""

import json

import re
import sys

#: A step is any statement carrying an `[id = N]` annotation. Block openers end
#: in `{`; leaves do not. The test declaration carries one too and is the root,
#: matched by the same pattern and placed by depth.
#:
#: The **last** match on the line is the step's identity, and the pattern is
#: deliberately not anchored to the end of the line. Both halves matter:
#:
#: - an argument can contain the token, as in
#:   `enterText("[id = 7]", element.a) [id = 2]`, so taking the first match read
#:   7 as the identity;
#: - the annotation is not always last, as in
#:   `enterText(env.appUsername, element.usernameField) [id = 1584] as username`,
#:   where `as <alias>` names the step's result. Anchoring to end-of-line
#:   dropped those steps from the tree entirely — not reported as faults and not
#:   reported as unchecked, which is the worst outcome available here.
_STEP = re.compile(r"\[id\s*=\s*(\d+)[^\]]*\]")


class Step:
    """One statement in a test, with its identity and its place in the tree.

    `identity` is the `[id = N]`. `order` is filled in from whatever numbering
    is being checked — the derived pre-order for the correct answer, or the
    platform's reported number when checking one. Keeping them separate is the
    whole correction: conflating them reports authoring history as a fault.
    """

    __slots__ = ("identity", "order", "parent", "line", "text", "children")

    def __init__(self, identity, parent, line, text):
        self.identity = identity
        self.order = None
        self.parent = parent
        self.line = line
        self.text = text
        self.children = []

    def __repr__(self):
        return f"Step(id={self.identity}, order={self.order}, line={self.line})"


def parse(text):
    """Return the root Step of a `.sigma` test, or None if it holds no steps.

    Parentage comes from the lexical nesting. Only the first `[id = N]` on a
    line is taken, so an argument that happens to contain the token cannot
    invent a step.
    """
    root = None
    stack = []
    seen = set()
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("//"):
            continue

        matches = list(_STEP.finditer(line))
        match = matches[-1] if matches else None
        opens = line.endswith("{")
        closes = line == "}"

        if closes:
            if stack:
                stack.pop()
            continue

        if match:
            identity = int(match.group(1))
            if identity in seen:
                raise ValueError(
                    f"line {number}: duplicate step id {identity}; a tree that "
                    f"loses a step silently cannot be checked"
                )
            seen.add(identity)
            step = Step(identity, stack[-1] if stack else None, number, line)
            if step.parent is not None:
                step.parent.children.append(step)
            elif root is None:
                root = step
            else:
                raise ValueError(
                    f"line {number}: a second step at the top level (id "
                    f"{identity}); it would belong to no tree and be checked by "
                    f"nothing"
                )
            if opens:
                stack.append(step)
        elif opens:
            # A block with no id of its own: keep the depth honest so the steps
            # inside it are not reparented to its grandparent.
            stack.append(stack[-1] if stack else None)
    if stack:
        raise ValueError(
            f"{len(stack)} block(s) left open at end of file; the parentage this "
            f"check depends on cannot be trusted"
        )
    return root


def walk(root):
    """Every step in the tree, in document order (a pre-order walk)."""
    out = []

    def visit(step):
        out.append(step)
        for child in step.children:
            visit(child)

    if root is not None:
        visit(root)
    return out


def derive_order(root):
    """The correct order: each step's position in the lexical pre-order walk.

    This is the authority. It comes from the working copy, which the Migration
    controls, rather than from the platform, which is what may be wrong.
    """
    return {step.identity: index for index, step in enumerate(walk(root))}


def apply_orders(root, orders):
    """Set each step's order from a mapping of step id to order number.

    Returns the ids in the tree that the mapping does not cover, because a step
    with no reported order is not a pass — it is an unanswered question about
    where that step ran.
    """
    missing = []
    for step in walk(root):
        if step.identity in orders:
            step.order = orders[step.identity]
        else:
            missing.append(step.identity)
    return missing


def _next_sibling(step):
    """The step after this one among its parent's children, or None."""
    if step.parent is None:
        return None
    siblings = step.parent.children
    index = siblings.index(step)
    return siblings[index + 1] if index + 1 < len(siblings) else None


def violations(root):
    """Every step whose order breaks the property.

    Each entry names the step, the window it had to fall inside, and why — a
    report saying only that a test is wrong cannot be acted on.
    """
    found = []
    for step in walk(root):
        for index, child in enumerate(step.children):
            if child.order is None or step.order is None:
                continue
            upper = _next_sibling(step)
            if child.order <= step.order:
                found.append(_fault(child, step, upper, "numbered before its own block"))
            elif upper is not None and upper.order is not None and child.order >= upper.order:
                found.append(
                    _fault(
                        child,
                        step,
                        upper,
                        "numbered outside its own block, so the block draws empty "
                        "and its steps run late",
                    )
                )
            previous = step.children[index - 1] if index else None
            if (
                previous is not None
                and previous.order is not None
                and child.order <= previous.order
            ):
                found.append(
                    _fault(
                        child,
                        step,
                        None,
                        f"out of document order against the step before it "
                        f"(order {previous.order})",
                    )
                )
    return found


def _fault(child, parent, upper, reason):
    return {
        "line": child.line,
        "id": child.identity,
        "order": child.order,
        "parent_order": parent.order,
        "limit": upper.order if upper is not None else None,
        "text": child.text,
        "reason": reason,
    }


def report(path, found):
    """A human-readable report of one file's violations."""
    lines = [f"{path}: {len(found)} step(s) out of place"]
    for entry in found:
        window = (
            f"after {entry['parent_order']}"
            if entry["limit"] is None
            else f"between {entry['parent_order']} and {entry['limit']}"
        )
        lines.append(
            f"  line {entry['line']} (id {entry['id']}): order {entry['order']} "
            f"must be {window} — {entry['reason']}"
        )
        lines.append(f"    {entry['text']}")
    return "\n".join(lines)


def main(argv):
    args = argv[1:]
    orders = None
    if "--orders" in args:
        index = args.index("--orders")
        try:
            with open(args[index + 1], encoding="utf-8") as handle:
                orders = {int(k): int(v) for k, v in json.load(handle).items()}
        except IndexError:
            sys.stderr.write("--orders needs a path to a JSON file\n")
            return 2
        args = args[:index] + args[index + 2 :]

    if not args:
        sys.stderr.write(__doc__)
        return 2

    failed = False
    for path in args:
        with open(path, encoding="utf-8") as handle:
            root = parse(handle.read())
        if root is None:
            print(f"{path}: no steps found")
            continue

        if orders is None:
            print(f"{path}: correct order, derived from the working copy")
            for identity, position in derive_order(root).items():
                print(f"  id {identity} -> {position}")
            continue

        missing = apply_orders(root, orders)
        if missing:
            failed = True
            print(f"{path}: no order reported for step(s) {missing} — not checked")
        found = violations(root)
        if found:
            failed = True
            print(report(path, found))
        elif not missing:
            print(f"{path}: order and nesting clean")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
