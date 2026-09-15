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


def run(tmp_path, steps, sigma, extra=()):
    (tmp_path / "steps.txt").write_text(steps, encoding="utf-8")
    (tmp_path / "t.test.sigma").write_text(textwrap.dedent(sigma), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--steps", str(tmp_path / "steps.txt"),
         *extra, str(tmp_path / "t.test.sigma")],
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
    #
    # The marker names its Cause. Before claims existed an empty block could
    # only be a marker, so the Cause was guidance; now that a label can claim
    # steps its body does not perform, it is what separates a marker from a
    # fake.
    marked = FULL.replace('      block "And I archive record \\"A1\\"" {\n        click(element["d"])\n      }',
                          '      block "And I archive record \\"A1\\" (Residue: declined — the customer keeps this manual)" {\n      }')
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

    def test_a_block_inside_a_block_is_reported(self, tmp_path):
        """TSF2079: a block holds steps, and a block is not a step.

        This was the tolerated shape until the tenant named it. It is not an
        *extra* — the outer block still claims its step — so it is reported as
        its own fault, with the flattening that repairs it.
        """
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
        assert r.returncode == 1, r.stdout
        assert "2 of 2" in r.stdout, "the outer block still claims its step"
        assert "match no source step" not in r.stdout
        assert "inside another block" in r.stdout

    def test_the_refusal_is_transitive_through_a_loop(self, tmp_path):
        """`block { for { block } }` is refused too.

        The app's blockParentId is inherited by descendants, so a loop between
        the two does not launder the nesting. A depth-counting walk that reset
        on the loop would miss exactly this.
        """
        nested = '''\
        test "x" {
          block "Given I am signed in" { click(element["a"]) }
          block "And Do the thing" {
            for row in tdp["D"] {
              block "Needs a step addon: no verb for this" {
              }
            }
          }
        }
        '''
        r = run(tmp_path, self.STEPS, nested)
        assert r.returncode == 1, r.stdout
        assert "inside another block" in r.stdout

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


class TestASliceIsCheckedBeforeTheNextOneStarts:
    """Assembly in slices, so no block is written at the far end of a long run.

    Every measured defect was the tail of a sequence — a helper's last action, a
    scenario's last steps — and the tail of a long test is written when the
    session is longest. A slice is assembled, checked and committed before the
    next begins, which makes the last block of each slice as near the source as
    the first.
    """

    STEPS = "Given one\nAnd two\nAnd three\nAnd four\n"
    HALF = '''\
    test "x" {
      block "Given one" { click(element.a) }
      block "And two" { click(element.b) }
    }
    '''

    def test_a_finished_slice_passes(self, tmp_path):
        r = run(tmp_path, self.STEPS, self.HALF, extra=["--through", "2"])
        assert r.returncode == 0, r.stdout
        assert "2 of 2" in r.stdout

    def test_the_same_file_fails_the_whole_scenario(self, tmp_path):
        """The slice passing must not read as the test being done."""
        r = run(tmp_path, self.STEPS, self.HALF)
        assert r.returncode == 1
        assert "And three" in r.stdout

    def test_writing_ahead_is_allowed(self, tmp_path):
        """A block for a later step is not an extra — leaving one behind is."""
        ahead = self.HALF.replace('block "And two" { click(element.b) }',
                                  'block "And two" { click(element.b) }\n'
                                  '      block "And four" { click(element.d) }')
        r = run(tmp_path, self.STEPS, ahead, extra=["--through", "2"])
        assert r.returncode == 0, r.stdout

    def test_a_step_skipped_inside_the_slice_still_fails(self, tmp_path):
        skipped = self.HALF.replace('block "Given one" { click(element.a) }', "")
        r = run(tmp_path, self.STEPS, skipped, extra=["--through", "2"])
        assert r.returncode == 1
        assert "Given one" in r.stdout


# --- one block claiming several source steps ---------------------------------

class TestAClaimMayAccountForSeveralSteps:
    """A target construct can absorb several source steps.

    Testsigma's `api` block *is* the request, its send and its assertions, so
    five Gherkin steps become one block. Before this, four of the five had no
    statement of their own and were assembled as empty blocks — the shape that
    means Residue, nobody could express this. Measured across four converted
    tests: 85 empty blocks, 79 of them absorbed rather than declined, so the
    real markers were outnumbered thirteen to one.

    A claim listing its steps restores the empty block to one meaning. The rule
    is a widening of what one label may account for, and of nothing else: a
    segment still matches a step exactly, or exactly with a bracketed qualifier.
    """

    ABSORBED = """\
Given I am signed in
When I set the request body
And I send the POST request
Then the response code is "200"
"""

    def test_one_label_accounts_for_every_step_it_lists(self, tmp_path):
        r = run(tmp_path, self.ABSORBED, '''\
            test "x" {
              block "Given I am signed in" {
                click(element["a"])
              }
              block "When I set the request body | And I send the POST request | Then the response code is \\"200\\"" {
                api "send" {
                  method = "POST"
                }
              }
            }
            ''')
        assert r.returncode == 0, r.stdout + r.stderr
        assert "accounted:    4 of 4" in r.stdout

    def test_the_steps_need_not_be_adjacent_in_the_source(self, tmp_path):
        # Measured: in one test the GET pattern repeats 18 times and 12 of the
        # absorbed steps sit a line or two after their absorber, because the
        # source interleaves a wait. A positional claim would be wrong there.
        steps = """\
When I send the GET request
And I wait for the spinner
Then I store the value from the response
"""
        r = run(tmp_path, steps, '''\
            test "x" {
              block "When I send the GET request | Then I store the value from the response" {
                api "get" {
                  method = "GET"
                }
              }
              block "And I wait for the spinner" {
                click(element["a"])
              }
            }
            ''')
        assert r.returncode == 0, r.stdout + r.stderr
        assert "accounted:    3 of 3" in r.stdout

    def test_a_segment_matching_no_source_step_is_reported(self, tmp_path):
        # The failure this must not become: a label that claims five steps and
        # writes one would invent coverage. A segment that matches nothing is
        # an extra, exactly as a whole label that matches nothing is.
        r = run(tmp_path, self.ABSORBED, '''\
            test "x" {
              block "Given I am signed in" {
                click(element["a"])
              }
              block "When I set the request body | POST /orders | And I send the POST request | Then the response code is \\"200\\"" {
                api "send" { method = "POST" }
              }
            }
            ''')
        assert r.returncode == 1
        assert "POST /orders" in r.stdout
        # Only the synthesised head is an extra. The four real steps beside it
        # are claimed, so this proves segments were matched rather than the
        # whole label failing as one — which is what happened before claims.
        assert "accounted:    4 of 4" in r.stdout

    def test_a_claim_does_not_satisfy_a_step_twice(self, tmp_path):
        # Coverage is a multiset. A label naming one step twice accounts for it
        # once, and the second mention is an extra.
        steps = "When I send the POST request\n"
        r = run(tmp_path, steps, '''\
            test "x" {
              block "When I send the POST request | When I send the POST request" {
                api "send" { method = "POST" }
              }
            }
            ''')
        # The second mention is refused rather than absorbed: a label claiming
        # a step it cannot perform twice is claiming coverage it does not have.
        assert r.returncode == 1
        assert "accounted:    1 of 1" in r.stdout
        assert "match no source step" in r.stdout

    def test_a_label_sharing_a_prefix_does_not_claim_the_step(self, tmp_path):
        # The module has always said "nothing looser, or an unrelated block
        # whose label happens to share a prefix would absorb a step it never
        # did" — and nothing held it to that. A mutation loosening the match to
        # a leading word passed the whole suite.
        steps = "When I press the key twice\n"
        r = run(tmp_path, steps, '''\
            test "x" {
              block "When I press" {
                click(element["a"])
              }
            }
            ''')
        assert r.returncode == 1
        assert "accounted:    0 of 1" in r.stdout
        assert "When I press" in r.stdout

    def test_a_segment_may_carry_a_bracketed_qualifier(self, tmp_path):
        steps = """\
When I send the POST request
Then the response code is "200"
"""
        r = run(tmp_path, steps, '''\
            test "x" {
              block "When I send the POST request (orders) | Then the response code is \\"200\\" (orders)" {
                api "send" { method = "POST" }
              }
            }
            ''')
        assert r.returncode == 0, r.stdout + r.stderr

    def test_a_step_whose_own_text_contains_the_separator_claims_itself(self, tmp_path):
        # The whole label is tried before it is split, so a claim widens what a
        # label may account for and changes nothing that already matched. An
        # earlier draft split unconditionally and turned this correct file into
        # two spurious extras and one unaccounted step.
        steps = "When I press a | b\n"
        r = run(tmp_path, steps, '''\
            test "x" {
              block "When I press a | b" {
                click(element["a"])
              }
            }
            ''')
        assert r.returncode == 0, r.stdout + r.stderr
        assert "accounted:    1 of 1" in r.stdout

    def test_a_qualifier_containing_the_separator_is_not_split(self, tmp_path):
        steps = "When I press the key\n"
        r = run(tmp_path, steps, '''\
            test "x" {
              block "When I press the key (a | b)" {
                click(element["a"])
              }
            }
            ''')
        assert r.returncode == 0, r.stdout + r.stderr

    def test_a_label_claiming_nothing_reaches_the_report(self, tmp_path):
        # `claimed()` once filtered empty segments, so a label of separators
        # returned no segments, the matching loop never ran, and the block left
        # the arithmetic entirely — neither matched nor reported.
        r = run(tmp_path, "When I press a\n", '''\
            test "x" {
              block "When I press a" {
                click(element["a"])
              }
              block " | " {
                click(element["b"])
              }
            }
            ''')
        assert r.returncode == 1
        assert "match no source step" in r.stdout


# --- an empty block must name a Cause -----------------------------------------

class TestAnEmptyBlockMustNameACause:
    """The last route to faking a conversion, once claims exist.

    Coverage reads labels and never read bodies, so a label naming five steps
    over a block that performs none accounted for all five. A marker and a fake
    were the same shape again — an empty block claiming work.

    The Cause separates them, and the count cannot: five consecutive declined
    steps are honestly one marker, so "an empty block claims at most one step"
    refuses a legitimate shape while a one-step fake still passes.
    """

    STEPS = """\
Given I am signed in
When I scan the barcode
Then I see the record
"""

    def test_an_empty_block_naming_a_cause_is_a_marker(self, tmp_path):
        r = run(tmp_path, self.STEPS, '''\
            test "x" {
              block "Given I am signed in" {
                click(element["a"])
              }
              block "When I scan the barcode (Residue: step addon — scan into the receiving field)" {
              }
              block "Then I see the record" {
                click(element["b"])
              }
            }
            ''')
        assert r.returncode == 0, r.stdout + r.stderr
        assert "accounted:    3 of 3" in r.stdout

    def test_an_empty_block_naming_no_cause_is_refused(self, tmp_path):
        r = run(tmp_path, self.STEPS, '''\
            test "x" {
              block "Given I am signed in" {
                click(element["a"])
              }
              block "When I scan the barcode | Then I see the record" {
              }
            }
            ''')
        assert r.returncode == 1
        assert "performs none" in r.stdout

    def test_a_marker_may_claim_a_run_of_declined_steps(self, tmp_path):
        # Why the count is not the test.
        r = run(tmp_path, self.STEPS, '''\
            test "x" {
              block "Given I am signed in" {
                click(element["a"])
              }
              block "When I scan the barcode | Then I see the record (Residue: declined — the customer converts these by hand)" {
              }
            }
            ''')
        assert r.returncode == 0, r.stdout + r.stderr
        assert "accounted:    3 of 3" in r.stdout

    def test_a_cause_outside_the_fixed_set_is_refused(self, tmp_path):
        # Otherwise "Residue: whatever I like" is a prefix that means nothing.
        r = run(tmp_path, self.STEPS, '''\
            test "x" {
              block "Given I am signed in" { click(element["a"]) }
              block "When I scan the barcode (Residue: too hard — no)" {
              }
              block "Then I see the record" { click(element["b"]) }
            }
            ''')
        assert r.returncode == 1
        assert "outside the fixed set" in r.stdout
        assert "too hard" in r.stdout

    def test_the_prefix_is_matched_case_sensitively(self, tmp_path):
        # The prefix is fixed so a reviewer can sweep for it. `residue:` passing
        # would mean a grep for `Residue:` misses a marker the checker blessed,
        # which is the whole argument for a fixed prefix undone quietly.
        r = run(tmp_path, self.STEPS, '''\
            test "x" {
              block "Given I am signed in" { click(element["a"]) }
              block "When I scan the barcode (residue: step addon — scan it)" {
              }
              block "Then I see the record" { click(element["b"]) }
            }
            ''')
        assert r.returncode == 1
        assert "name no Cause" in r.stdout

    def test_a_block_left_open_at_the_end_is_still_judged(self, tmp_path):
        # `empty` was appended only when a block closed, so a truncated file's
        # last block escaped the judgement every other block gets.
        r = run(tmp_path, "Given I am signed in\n", '''\
            test "x" {
              block "Given I am signed in" {
            ''')
        assert r.returncode == 1
        assert "name no Cause" in r.stdout

    def test_a_block_with_a_body_is_not_refused_for_lacking_a_cause(self, tmp_path):
        r = run(tmp_path, self.STEPS, '''\
            test "x" {
              block "Given I am signed in" { click(element["a"]) }
              block "When I scan the barcode" { click(element["c"]) }
              block "Then I see the record" { click(element["b"]) }
            }
            ''')
        assert r.returncode == 0, r.stdout + r.stderr

    def test_a_cause_on_a_block_with_a_body_is_a_partly_converted_step(self, tmp_path):
        # The rule is one-way. A block that converts what it can and names the
        # remainder is how the format refuses a Divergence — the case most often
        # missed, since such a block reads as fully converted. An earlier draft
        # of this check refused it, which would have made the honest shape
        # unwritable.
        r = run(tmp_path, self.STEPS, '''\
            test "x" {
              block "Given I am signed in" { click(element["a"]) }
              block "When I scan the barcode (Residue: step addon — scan into the receiving field)" {
                click(element["c"])
              }
              block "Then I see the record" { click(element["b"]) }
            }
            ''')
        assert r.returncode == 0, r.stdout + r.stderr
        assert "accounted:    3 of 3" in r.stdout
