"""The coverage check: does the assembled test account for its whole scenario?

ADR-0010 adds this as the first of six checks. The measured failure it exists to
catch is the one that defeated all five of the others: nine steps of fifty-five
converted, reported as "all 7 steps", compiling, pushing and round-tripping
clean with an empty Residue table.

These run the script rather than asserting prose about it. A check whose own
tests only read the document that describes it is the shape of thing that passes
while the mechanism is broken.
"""

import subprocess
import sys
import textwrap

import pytest

from support import PLUGIN_ROOT

SCRIPT = PLUGIN_ROOT / "scripts" / "check_coverage.py"

STEPS = """\
Given I am signed in
When I search for record "A1"
Then I see the record "A1" in the list
And I archive record "A1"
"""


def run(tmp_path, steps, sigma):
    (tmp_path / "steps.txt").write_text(steps, encoding="utf-8")
    (tmp_path / "t.test.sigma").write_text(textwrap.dedent(sigma), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--steps", str(tmp_path / "steps.txt"),
         str(tmp_path / "t.test.sigma")],
        capture_output=True, text=True,
    )


FULL = '''\
    test "x" {
      block "Given I am signed in" {
        click(element["a"])
      }
      block "When I search for record \\"A1\\"" {
        click(element["b"])
      }
      block "Then I see the record \\"A1\\" in the list" {
        click(element["c"])
      }
      block "And I archive record \\"A1\\"" {
        click(element["d"])
      }
    }
'''


def test_it_exists_and_is_executable():
    assert SCRIPT.is_file()


def test_a_complete_conversion_passes(tmp_path):
    r = run(tmp_path, STEPS, FULL)
    assert r.returncode == 0, r.stdout
    assert "4 of 4" in r.stdout


def test_coverage_is_reported_even_when_it_is_right(tmp_path):
    # A number printed only on failure is one nobody learns to read, and this
    # failure's character was that every visible signal looked normal.
    r = run(tmp_path, STEPS, FULL)
    assert "accounted:" in r.stdout


def test_a_dropped_step_is_named(tmp_path):
    partial = FULL.replace(
        '      block "And I archive record \\"A1\\"" {\n        click(element["d"])\n      }\n', ""
    )
    r = run(tmp_path, STEPS, partial)
    assert r.returncode == 1
    assert "3 of 4" in r.stdout
    assert "I archive record" in r.stdout, "the missing step must be named, not counted"


def test_an_empty_marker_counts_as_accounted(tmp_path):
    # Residue and conversion both count. A declined step that stands as a marker
    # is accounted for; only silence is not.
    marked = FULL.replace('      block "And I archive record \\"A1\\"" {\n        click(element["d"])\n      }',
                          '      block "And I archive record \\"A1\\"" {\n      }')
    r = run(tmp_path, STEPS, marked)
    assert r.returncode == 0, r.stdout


def test_a_test_with_no_blocks_at_all_is_refused(tmp_path):
    """The measured failure's exact shape: bare statements, nothing to compare.

    Returning 0 here would be the worst possible answer — the check would report
    success on the one file it was written for.
    """
    bare = '''\
    test "x" {
      click(element["a"])
      click(element["b"])
    }
'''
    r = run(tmp_path, STEPS, bare)
    assert r.returncode == 1, r.stdout
    assert "silence is not a pass" in r.stdout


def test_the_keyword_is_not_part_of_a_step_s_identity(tmp_path):
    # `And Search ASN` and `When Search ASN` are one step. Both sides are
    # normalised, so the comparison is symmetric.
    swapped = FULL.replace('block "Given I am signed in"', 'block "And I am signed in"')
    r = run(tmp_path, STEPS, swapped)
    assert r.returncode == 0, r.stdout


def test_a_nested_block_still_claims_its_step(tmp_path):
    # Counting only top-level blocks would report a correctly nested conversion
    # as incomplete.
    nested = FULL.replace(
        '      block "And I archive record \\"A1\\"" {\n        click(element["d"])\n      }',
        '      if elementIs(element["x"], "visible") {\n'
        '        block "And I archive record \\"A1\\"" {\n'
        '          click(element["d"])\n        }\n      }',
    )
    r = run(tmp_path, STEPS, nested)
    assert r.returncode == 0, r.stdout


def test_a_block_matching_no_source_step_is_reported(tmp_path):
    invented = FULL.replace('block "Given I am signed in"', 'block "And I do something nobody asked for"')
    r = run(tmp_path, STEPS, invented)
    assert r.returncode == 1
    assert "nobody asked for" in r.stdout
