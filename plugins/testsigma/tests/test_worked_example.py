"""The worked example, checked against a written-down expectation.

Measured runs spent validates rediscovering the shape of a correct file: four on
the screen file and element declaration, two on whether an `if` header takes
parentheses. None of it is in any listing — `list blocks` gives a block's
grammar, not what a correct file looks like end to end — so it is the one
category where writing something down is the answer rather than a stale copy.

**This is a source check, not a residue check.** The expectation below is
written out independently and the file is compared against it. The obvious
alternative — "every construct I demonstrate appears in the result" — has the
blind spot `checks.md` describes: it cannot notice half the shape missing,
which would make a demonstration of correctness that could itself be half wrong.

`validate` runs against the real CLI where one is installed, and skips where it
is not. The skip is why the structural assertions do not lean on it.
"""

import pathlib
import shutil
import subprocess

import pytest

from support import PLUGIN_ROOT

EXAMPLE = PLUGIN_ROOT / "examples" / "worked"
VERSION = EXAMPLE / "tests/testsigma/exampleProject/exampleApp/v1"

#: Every shape the example exists to demonstrate, with where it is demonstrated.
#: Named individually so a removal names itself rather than moving a count.
SHAPES = {
    "screen file nests elements": (
        "elements/SignIn.screen.sigma", 'screen "SignIn" {'),
    "element carries locator and locatorType": (
        "elements/SignIn.screen.sigma", 'locatorType = "xpath"'),
    "a dynamic element takes a parameter reference": (
        "elements/SignIn.screen.sigma", 'dynamic = true'),
    "dotted reference for an identifier-safe name": (
        "tests/Demo/SignIn.test.sigma", "element.usernameField"),
    "bracket reference for a name with spaces": (
        "tests/Demo/SignIn.test.sigma", 'element["sign in button"]'),
    "an if header takes no parentheses": (
        "tests/Demo/SignIn.test.sigma", 'if elementIs(element["sign in button"], "visible") {'),
    "a setting rides in brackets after the arguments": (
        "tests/Demo/SignIn.test.sigma", "[timeout = 60]"),
    "a marker is the step's own block, its Cause and need in the label": (
        "tests/Demo/SignIn.test.sigma", '(Residue: step addon —'),
    "a test binds a profile": (
        "tests/Demo/SignIn.test.sigma", 'profile = tdp["SignInData"].set('),
}


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_the_example_demonstrates(shape):
    where, needle = SHAPES[shape]
    text = (VERSION / where).read_text(encoding="utf-8")
    assert needle in text, f"{shape}: {needle!r} is not in {where}"


def test_elements_are_in_canonical_alphabetical_order():
    """The seventh shape, and the one no measured run found.

    Runs stopped at "no errors" and never reached warnings-clean, so none of
    them learned that a screen's elements are ordered by name. An example that
    validates with a TSF3001 teaches a file the next pull rewrites.
    """
    import re
    text = (VERSION / "elements/SignIn.screen.sigma").read_text(encoding="utf-8")
    names = re.findall(r'^\s*element\s+"([^"]+)"', text, re.M)
    assert names == sorted(names), f"elements are not in name order: {names}"


def test_the_marker_is_a_block_and_there_are_no_groups():
    """A measured run wrote `group "…" { }` for a marker.

    It validates offline and is refused at push with TSS1102, because a group
    invocation needs a step group of that name to exist. The example must not
    contain the shape that fails, or it teaches it.
    """
    text = (VERSION / "tests/Demo/SignIn.test.sigma").read_text(encoding="utf-8")
    assert 'group "' not in text


@pytest.mark.skipif(shutil.which("testsigma") is None, reason="no CLI installed")
def test_the_example_validates_with_no_errors_and_no_warnings():
    """Warnings matter here in a way they do not elsewhere.

    A TSF3001 or TSF3004 means the next `pull` rewrites the file, so an example
    carrying one demonstrates a layout the tool disagrees with.
    """
    r = subprocess.run(["testsigma", "validate"], cwd=EXAMPLE,
                       capture_output=True, text=True)
    output = r.stdout + r.stderr
    assert "error" not in output, output
    assert "warning" not in output, output


def test_the_authoring_reference_points_at_the_example():
    """An example nothing points at is one nobody reads.

    A measured run searched the plugin for `.sigma` files before writing its
    first one, found none, and reconstructed the shape by trial.
    """
    from support import REFERENCES_DIR
    text = (REFERENCES_DIR / "authoring.md").read_text(encoding="utf-8")
    assert "examples/worked/" in text


def test_no_block_contains_another_block():
    """The tenant has no nested blocks, and the example is what gets copied.

    An earlier version of this file nested the marker inside the step's block,
    which read well and is refused at the wire. A worked example carrying a
    shape the CLI rejects teaches the one thing it exists to prevent.
    """
    import re
    text = (VERSION / "tests/Demo/SignIn.test.sigma").read_text(encoding="utf-8")
    depth = 0
    block_depth = None
    for line in text.split("\n"):
        if re.match(r'^\s*block\s+"', line):
            assert block_depth is None, f"a block opens inside a block: {line.strip()}"
            block_depth = depth
        depth += line.count("{") - line.count("}")
        if block_depth is not None and depth <= block_depth:
            block_depth = None
