"""The Cucumber adapter's stated rule must produce its stated counts.

This is the check that makes "precise enough that two people applying it get the
same count" verifiable. `tests/gherkin.py` is the adapter's normalisation rule
written out as code; if the document's rule and its worked example ever drift
apart, this fails.

It also guards the fixture. Ticket 13's behavioural evals depend on the fixture
still containing the three traps, and a fixture quietly simplified would make
those evals pass while proving nothing.
"""

import pytest

from gherkin import distinct_source_steps, total_step_occurrences
from support import (
    ADAPTERS_DIR,
    FIXTURES_DIR,
    has_paragraph_with,
    markdown_sections,
    parse_count_table,
    read_frontmatter,
)

ADAPTER = ADAPTERS_DIR / "cucumber-java.md"
FIXTURE = FIXTURES_DIR / "cucumber-java"


@pytest.fixture(scope="module")
def feature_texts():
    features = sorted((FIXTURE / "features").glob("*.feature"))
    assert features, f"no feature files in {FIXTURE / 'features'}"
    return [path.read_text(encoding="utf-8") for path in features]


@pytest.fixture(scope="module")
def stated_table():
    _, body = read_frontmatter(ADAPTER)
    table = parse_count_table(markdown_sections(body)["Enumeration"])
    assert table, "the adapter's Enumeration section has no worked example table"
    return table


# --- the fixture exists and still contains its traps ------------------------

def test_the_fixture_suite_exists():
    assert (FIXTURE / "features").is_dir()
    assert (FIXTURE / "pages").is_dir()
    assert sorted(p.name for p in (FIXTURE / "pages").glob("*.java")), "no page objects"


def test_the_fixture_carries_locators_as_the_adapter_claims():
    meta, _ = read_frontmatter(ADAPTER)
    assert meta["carries-locators"] == "yes"
    pages = "\n".join(p.read_text(encoding="utf-8") for p in (FIXTURE / "pages").glob("*.java"))
    assert "@FindBy" in pages, "the adapter claims this source carries locators"


def test_the_helper_that_does_more_than_its_line_implies_is_still_there():
    source = (FIXTURE / "pages" / "SearchPage.java").read_text(encoding="utf-8")
    assert "if (" in source, "the conditional expand is the point of this fixture"
    assert ".clear()" in source
    assert "ENTER" in source


def test_the_helper_that_does_less_than_its_line_implies_is_still_there():
    source = (FIXTURE / "pages" / "ReceivingPage.java").read_text(encoding="utf-8")
    assert "sendKeys" in source
    # The trap is that the submit control exists and is never clicked.
    assert "reasonSubmit" in source
    assert "reasonSubmit.click()" not in source


def test_the_wait_named_helper_that_is_really_a_loop_is_still_there():
    source = (FIXTURE / "pages" / "JournalPage.java").read_text(encoding="utf-8")
    assert "refreshUntil" in source
    assert "for (" in source or "while (" in source, "this helper must be a loop"
    assert "refreshButton.click()" in source, "a loop that re-drives the interface"


def test_the_delegating_helper_is_still_there():
    # The adapter instructs the reader to follow a nested call. Without a
    # fixture that has one, ticket 13's evals cannot tell whether an agent
    # follows delegation or stops at the first method it opens.
    source = (FIXTURE / "pages" / "PutawayPage.java").read_text(encoding="utf-8")
    assert "searchPage.searchForLpn" in source, "the delegation is the point"
    assert "confirmButton.click()" in source, "it must also act in its own right"


# --- the document's claims match the executable rule ------------------------

def test_the_stated_counts_are_exactly_what_the_rule_produces(feature_texts, stated_table):
    assert stated_table == distinct_source_steps(feature_texts)


def test_the_stated_counts_sum_to_the_fixture_step_lines(feature_texts, stated_table):
    assert sum(stated_table.values()) == total_step_occurrences(feature_texts)


def test_the_rule_collapses_an_outline_placeholder_onto_its_quoted_twin(feature_texts):
    # The fixture contains both spellings of one search step, once quoted and
    # once as a Scenario Outline placeholder. They must be one Source Step.
    counts = distinct_source_steps(feature_texts)
    assert counts['I search for LPN "<param>"'] == 2


def test_the_documented_textual_limit_is_real(feature_texts):
    # The adapter warns that the rule is textual, so singular and plural are
    # different Source Steps. If that stops being true the warning is stale.
    counts = distinct_source_steps(feature_texts)
    assert "I see <number> result" in counts
    assert "I see <number> results" in counts


class TestARuntimeBuiltLocatorIsJudgedRatherThanRefused:
    """A verification pass contradicted the rule this adapter first stated.

    It said a runtime-built locator always means an unresolved element.
    Materialising one turned out to be correct where the source names a single
    value, and refusing it would have blocked a test that had everything it
    needed.
    """

    def _locators(self):
        _, body = read_frontmatter(ADAPTERS_DIR / "cucumber-java.md")
        return markdown_sections(body)["Locators"]

    def test_the_decision_turns_on_whether_the_values_are_enumerable(self):
        assert has_paragraph_with(self._locators(), "enumerable", "call sites")

    def test_an_enumerable_value_is_materialised_rather_than_refused(self):
        assert has_paragraph_with(
            self._locators(),
            "materialise",
            "right call",
            absent=("always treat", "never materialise"),
        ), "refusing a fully determined element blocks a test that is fine"

    def test_enumerability_decides_it_rather_than_the_call_site_count(self):
        # Review: the analysis only examined a single-site, single-literal case,
        # so making the count the deciding factor was an extrapolation. Many
        # sites each passing a known literal are still enumerable.
        assert has_paragraph_with(
            self._locators(), "enumerability is what decides it"
        )
        assert has_paragraph_with(
            self._locators(), "many call sites", "still enumerable"
        )

    def test_a_value_the_source_computes_at_run_time_stays_unresolved(self):
        assert has_paragraph_with(self._locators(), "computed at run time", "unresolved")

    def test_the_judgement_is_reported_so_it_can_be_corrected(self):
        assert has_paragraph_with(self._locators(), "say which", "call sites")
