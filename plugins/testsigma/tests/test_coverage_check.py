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


class TestADuplicatedStepIsCountedTwice:
    """Coverage is a multiset. The first version treated it as a set.

    `Click on Row At First Index` occurs twice in the measured scenario. With
    set membership, converting it once satisfied both occurrences — the check
    reported "4 of 4" while printing "blocks: 3" two lines above, which is the
    failure it exists to refuse, reproduced inside it.
    """

    STEPS = "Given I am signed in\nAnd Click a row\nAnd Something else\nAnd Click a row\n"

    def test_converting_a_duplicated_step_once_is_refused(self, tmp_path):
        once = '''\
        test "x" {
          block "Given I am signed in" { click(element["a"]) }
          block "And Click a row" { click(element["b"]) }
          block "And Something else" { click(element["c"]) }
        }
        '''
        r = run(tmp_path, self.STEPS, once)
        assert r.returncode == 1, r.stdout
        assert "3 of 4" in r.stdout

    def test_converting_it_twice_passes(self, tmp_path):
        twice = '''\
        test "x" {
          block "Given I am signed in" { click(element["a"]) }
          block "And Click a row" { click(element["b"]) }
          block "And Something else" { click(element["c"]) }
          block "And Click a row" { click(element["d"]) }
        }
        '''
        r = run(tmp_path, self.STEPS, twice)
        assert r.returncode == 0, r.stdout
        assert "4 of 4" in r.stdout

    def test_a_disambiguating_suffix_still_claims_its_step(self, tmp_path):
        # Two identical steps in one scenario read better with a qualifier, and
        # the measured run wrote `… (PIX Visibility)` for the second. Good
        # authoring must not be scored as an unmatched block.
        suffixed = '''\
        test "x" {
          block "Given I am signed in" { click(element["a"]) }
          block "And Click a row" { click(element["b"]) }
          block "And Something else" { click(element["c"]) }
          block "And Click a row (PIX Visibility)" { click(element["d"]) }
        }
        '''
        r = run(tmp_path, self.STEPS, suffixed)
        assert r.returncode == 0, r.stdout
        assert "4 of 4" in r.stdout

    def test_an_unrelated_block_is_not_absorbed_by_a_shared_prefix(self, tmp_path):
        # The suffix rule must stay narrow: only a trailing bracketed qualifier.
        # Anything looser and a block that merely starts the same way would
        # silently claim a step it never converted.
        looser = '''\
        test "x" {
          block "Given I am signed in" { click(element["a"]) }
          block "And Click a row" { click(element["b"]) }
          block "And Something else" { click(element["c"]) }
          block "And Click a row and then do three other things" { click(element["d"]) }
        }
        '''
        r = run(tmp_path, self.STEPS, looser)
        assert r.returncode == 1, r.stdout
        assert "3 of 4" in r.stdout


class TestANestedMarkerIsDetailNotAClaim:
    """A marker inside a step's block explains that step; it claims nothing.

    The structure a real conversion produced, and it is better than a flat file
    because the marker sits where the missing work belongs:

        block "Validate list of UI values …"
            block "Needs a step addon: check all 10 values …"

    Counting the inner one as a block matching no source step made the check
    exit 1 on a complete 55-of-55 conversion. The run read that, correctly
    called the extras informational, and carried on — a check teaching its
    reader to disregard it, which is worse than not having run.
    """

    STEPS = "Given I am signed in\nAnd Do the thing\n"

    def test_a_marker_nested_in_a_claiming_block_is_not_an_extra(self, tmp_path):
        nested = '''\
        test "x" {
          block "Given I am signed in" { click(element["a"]) }
          block "And Do the thing" {
            block "Needs a step addon: no verb for this" {
            }
          }
        }
        '''
        r = run(tmp_path, self.STEPS, nested)
        assert r.returncode == 0, r.stdout
        assert "2 of 2" in r.stdout
        assert "match no source step" not in r.stdout

    def test_a_step_block_inside_a_conditional_still_claims(self, tmp_path):
        """Depth is not the rule; a *claiming parent* is.

        Only counting top-level blocks would call a correctly nested conversion
        incomplete, so an `if` around a step's block must not suppress it.
        """
        conditional = '''\
        test "x" {
          block "Given I am signed in" { click(element["a"]) }
          if elementIs(element["x"], "visible") {
            block "And Do the thing" { click(element["b"]) }
          }
        }
        '''
        r = run(tmp_path, self.STEPS, conditional)
        assert r.returncode == 0, r.stdout
        assert "2 of 2" in r.stdout

    def test_an_invented_top_level_block_is_still_reported(self, tmp_path):
        # The rule must not become "ignore anything unmatched" — a top-level
        # block that claims nothing in the source is still a step nobody asked
        # for, and that is what the extras list is for.
        invented = '''\
        test "x" {
          block "Given I am signed in" { click(element["a"]) }
          block "And Do the thing" { click(element["b"]) }
          block "And something nobody asked for" { click(element["c"]) }
        }
        '''
        r = run(tmp_path, self.STEPS, invented)
        assert r.returncode == 1, r.stdout
        assert "nobody asked for" in r.stdout
