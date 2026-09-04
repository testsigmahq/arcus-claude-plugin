"""Tests for the Gherkin reading used to check an adapter's stated counts.

This is test tooling, not part of the plugin. A Source Adapter is a document an
agent reads (ADR-0004); nothing here ships. Its only job is to make the
adapter's normalisation rule executable, so "precise enough that two people
applying it get the same count" is a property the suite can verify rather than a
claim in prose.
"""

import pytest

from gherkin import (
    UnsupportedLanguage,
    distinct_source_steps,
    normalise_step,
    step_lines,
)


# --- step_lines --------------------------------------------------------------

def test_finds_steps_and_drops_everything_else():
    feature = """Feature: Ordering
  Background:
    Given I am signed in
  Scenario: Place an order
    # a comment
    When I search for "widget"
    Then I see 3 results
    And I see "widget" in the list
"""
    assert step_lines(feature) == [
        "Given I am signed in",
        'When I search for "widget"',
        "Then I see 3 results",
        'And I see "widget" in the list',
    ]


def test_ignores_docstrings_and_data_tables():
    feature = '''Feature: F
  Scenario: S
    Given a payload
      """
      When this line is inside a docstring it is not a step
      """
    Then I see a table
      | name  | value |
      | Given | not a step |
'''
    assert step_lines(feature) == ["Given a payload", "Then I see a table"]


def test_a_bullet_step_line_is_found():
    assert step_lines("Feature: F\n  Scenario: S\n    * I do a thing\n") == [
        "* I do a thing"
    ]


def test_a_keyword_must_be_a_whole_word_at_the_start():
    feature = """Feature: F
  Scenario: S
    Given a thing
    Givenish not a step
    Something Given not a step
"""
    assert step_lines(feature) == ["Given a thing"]


def test_a_localised_feature_file_is_refused_rather_than_read_as_empty():
    # Returning no steps would report a Collapse Ratio of nothing, which reads
    # as an answer rather than as a failure to read the file.
    german = "# language: de\nFunktionalitaet: F\n  Szenario: S\n    Gegeben sei ein Ding\n"
    with pytest.raises(UnsupportedLanguage):
        step_lines(german)


def test_an_explicit_english_pragma_is_accepted():
    assert step_lines("# language: en\nFeature: F\n  Scenario: S\n    Given a thing\n") == [
        "Given a thing"
    ]


# --- normalise_step ----------------------------------------------------------

def test_drops_the_keyword_so_and_matches_given():
    assert normalise_step("Given I am signed in") == normalise_step("And I am signed in")


def test_replaces_a_double_quoted_span_with_a_placeholder():
    assert normalise_step('When I search for "widget"') == 'I search for "<param>"'


def test_replaces_a_single_quoted_span_with_a_placeholder():
    # Quoting style is not part of a Source Step's identity, so a single-quoted
    # literal collapses onto the same placeholder as a double-quoted one.
    assert normalise_step("When I search for 'widget'") == 'I search for "<param>"'
    assert normalise_step("When I search for 'widget'") == normalise_step(
        'When I search for "widget"'
    )


def test_apostrophes_in_ordinary_prose_are_not_parameters():
    assert normalise_step("Then I don't see the user's name") == (
        "I don't see the user's name"
    )


def test_a_placeholder_inside_a_quoted_span_does_not_nest():
    assert normalise_step('When I open a "quoted <term> inside"') == 'I open a "<param>"'


def test_a_comma_grouped_number_is_one_number():
    assert normalise_step("When I search for 1,000 items") == "I search for <number> items"


def test_a_bullet_step_is_a_step():
    assert normalise_step("* I do a thing") == "I do a thing"


def test_replaces_numbers_with_a_placeholder():
    assert normalise_step("Then I see 3 results") == "I see <number> results"
    assert normalise_step("Then I wait 2.5 seconds") == "I wait <number> seconds"


def test_replaces_a_scenario_outline_placeholder():
    assert normalise_step("When I search for <term>") == 'I search for "<param>"'


def test_collapses_internal_whitespace_and_trims():
    assert normalise_step("  When   I   search  for   x  ") == "I search for x"


def test_a_number_abutting_a_full_stop_is_still_a_number():
    # The number pattern refuses a digit next to a dot so a version-like 1.2.3
    # survives. That must not leave a sentence-ending stop splitting one step
    # into two.
    assert normalise_step("Then I see 5.") == normalise_step("Then I see 5")
    assert normalise_step("Then I see 5.") == "I see <number>"


def test_a_version_like_number_is_left_alone():
    assert normalise_step("Then I see 1.2.3") == "I see 1.2.3"


def test_an_unterminated_quote_is_left_as_written():
    # Pinned so a future change to the quote passes cannot alter it silently.
    assert normalise_step('Then I see "unterminated') == 'I see "unterminated'
    assert normalise_step("Then I see 'unterminated") == "I see 'unterminated"


def test_double_quotes_are_replaced_before_single_quotes():
    # A single-quoted word inside a double-quoted span is part of that span.
    # If the passes ran the other way round this would produce two parameters.
    line = "Then I see " + chr(34) + "it's a 'nested' word" + chr(34)
    assert normalise_step(line) == 'I see "<param>"'


def test_a_number_inside_a_word_is_not_a_placeholder():
    # Identifiers like ILPN05 are part of the phrasing, not a parameter.
    assert normalise_step("When I open ILPN05") == "I open ILPN05"


def test_two_lines_differing_only_in_their_literals_are_one_source_step():
    a = normalise_step('When I search for "widget" and see 3 results')
    b = normalise_step('When I search for "gadget" and see 12 results')
    assert a == b


def test_trailing_punctuation_does_not_split_a_step():
    assert normalise_step("Given I am signed in.") == normalise_step("Given I am signed in")


def test_a_line_that_is_not_a_step_is_refused():
    with pytest.raises(ValueError):
        normalise_step("Feature: Ordering")


# --- distinct_source_steps ---------------------------------------------------

def test_counts_occurrences_of_each_distinct_source_step():
    feature = """Feature: F
  Scenario: A
    Given I am signed in
    When I search for "widget"
  Scenario: B
    Given I am signed in
    When I search for "gadget"
    And I search for "cog"
"""
    assert distinct_source_steps([feature]) == {
        "I am signed in": 2,
        'I search for "<param>"': 3,
    }


def test_counts_across_several_files():
    one = "Feature: F\n  Scenario: S\n    Given a thing\n"
    two = "Feature: G\n  Scenario: T\n    Given a thing\n    When another\n"
    assert distinct_source_steps([one, two]) == {"a thing": 2, "another": 1}
