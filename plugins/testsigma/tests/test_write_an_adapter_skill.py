"""The write-an-adapter skill: producing a third Source Adapter without us.

The two shipped adapters are the worked examples, and they earn that role by
sitting at opposite corners of all three properties. This skill's job is to walk
an author to a document that passes the same suite the shipped ones pass.
"""

import pytest

from support import (
    ADAPTERS_DIR,
    PLUGIN_ROOT,
    REQUIRED_ADAPTER_SECTIONS,
    THREE_PROPERTIES,
    adapter_files,
    has_paragraph_with,
    hedges_in,
    markdown_sections,
    read_frontmatter,
)

SKILL = PLUGIN_ROOT / "skills" / "write-an-adapter" / "SKILL.md"

LOAD_BEARING = ("three properties", "normalisation", "sequence", "documentation")


def _body():
    _, body = read_frontmatter(SKILL)
    return body


def _sections():
    return markdown_sections(_body())


def _section(needle):
    matching = [v for k, v in _sections().items() if needle in k.lower()]
    assert len(matching) == 1, (
        f"expected exactly one section whose heading contains {needle!r}, found "
        f"{len(matching)}. Headings are: {list(_sections())}"
    )
    return matching[0]


class TestTheSkillExists:
    def test_it_exists(self):
        assert SKILL.is_file()

    def test_its_description_says_it_writes_an_adapter(self):
        meta, _ = read_frontmatter(SKILL)
        description = str(meta.get("description", "")).lower()
        assert "adapter" in description
        assert "source" in description


class TestItProducesADocumentThatPassesTheContract:
    def test_it_points_at_the_contract_rather_than_restating_it(self):
        assert "adapters/README.md" in _body(), (
            "the contract has one definition; a second copy is drift waiting to happen"
        )

    def test_it_says_the_suite_is_what_decides_the_document_is_done(self):
        assert has_paragraph_with(
            _body(), "suite", "pass"
        ), "an adapter is finished when the adapter tests pass, not when it reads well"

    @pytest.mark.parametrize("section", REQUIRED_ADAPTER_SECTIONS)
    def test_it_names_each_required_section(self, section):
        assert section.lower() in _body().lower(), (
            f"an author is not told the {section} section is required"
        )

    def test_it_requires_a_worked_example_checked_against_a_fixture(self):
        assert has_paragraph_with(_body(), "fixture", "worked example")

    def test_it_requires_every_row_in_the_worked_example(self):
        assert has_paragraph_with(
            _body(), "every row", "partial"
        ), "a partial table cannot be checked against the rule that produced it"


class TestTheThreePropertiesCannotBeLeftUnstated:
    @pytest.mark.parametrize("prop", THREE_PROPERTIES)
    def test_each_property_is_named(self, prop):
        assert prop in _section("three properties")

    def test_an_explicit_value_is_required_for_each(self):
        assert has_paragraph_with(
            _section("three properties"), "explicit value", "unstated"
        ), "a property left unstated is the one that decides the Phase structure"

    def test_it_says_to_quote_the_value(self):
        # Unquoted yes and no are YAML booleans, and the point of the field is
        # that somebody stated it deliberately.
        assert has_paragraph_with(_section("three properties"), "quote", "boolean")

    def test_sometimes_is_allowed_but_must_be_explained(self):
        assert has_paragraph_with(_section("three properties"), "sometimes", "how to tell")

    def test_the_properties_are_independent_so_none_is_inferred(self):
        assert has_paragraph_with(_section("three properties"), "independent")


class TestTheNormalisationRule:
    def test_a_stated_rule_is_required(self):
        assert has_paragraph_with(
            _section("normalisation"), "same source step"
        )

    def test_it_must_be_reproducible_by_two_people(self):
        assert has_paragraph_with(
            _section("normalisation"),
            "two people",
            absent=("roughly the same",),
        ), "a rule two readers apply differently is not a rule"

    def test_it_must_be_ordered_steps(self):
        # Order matters: a rule that strips punctuation after replacing numbers
        # gives different answers from one that does it before.
        assert has_paragraph_with(_section("normalisation"), "order")

    def test_it_warns_that_the_order_of_the_steps_changes_the_answer(self):
        assert has_paragraph_with(
            _section("normalisation"), "order of the steps changes the answer"
        ), "the Cucumber rule had exactly this bug"


class TestWhereTrueSequenceLives:
    def test_the_author_must_find_where_sequence_lives(self):
        assert has_paragraph_with(_section("sequence"), "where", "sequence")

    def test_it_must_be_stated_even_when_nothing_is_hidden(self):
        assert has_paragraph_with(
            _section("sequence"),
            "nothing",
            "say",
            absent=("skip the section", "leave the section out"),
        ), "a silent Sequence section is indistinguishable from an unasked question"

    def test_a_helper_is_opened_for_sequence_and_not_only_for_locators(self):
        assert has_paragraph_with(_section("sequence"), "not only", "locator")


class TestTheTwoShippedAdaptersAreTheExamples:
    def test_both_are_referenced_by_name(self):
        body = _body()
        for adapter in adapter_files():
            assert adapter.name in body, f"{adapter.name} is not offered as an example"

    def test_their_opposing_values_are_called_out(self):
        section = _section("shipped adapters")
        assert has_paragraph_with(section, "opposite") or has_paragraph_with(
            section, "inverse"
        ), "the two adapters are useful as examples because they oppose on all three"

    def test_the_example_table_states_both_adapters_values(self):
        # A reader picking an example needs to know which one resembles their
        # source, which means seeing both sets of values.
        section = _section("shipped adapters")
        assert section.count("yes") >= 3 and section.count("no") >= 3


class TestItDistrustsPublishedDocumentation:
    def test_it_warns_that_documentation_may_be_wrong(self):
        assert has_paragraph_with(
            _section("documentation"), "documentation", "may be wrong"
        )

    def test_it_gives_the_case_where_documentation_was_wrong_twice(self):
        section = _section("documentation")
        # Described as opaque binary, and is readable gzipped JSON.
        assert has_paragraph_with(section, "binary", "json")
        # Identification described as living on module attributes the real
        # export does not contain at all.
        assert "xmoduleattribute" in section.lower().replace(" ", "")

    def test_it_requires_opening_a_real_export_first(self):
        assert has_paragraph_with(
            _section("documentation"), "real export", "before writing"
        ), "the export is read before the document is written"

    def test_it_refuses_to_write_an_adapter_from_a_specification(self):
        # The primary rule above survived deleting this refusal, leaving the
        # section contradicting itself: read a real export first, and also
        # write from the specification when you cannot get one.
        assert has_paragraph_with(
            _section("documentation"), "stop", "specification"
        ), "with no export the answer is to stop, not to write from a document"


@pytest.mark.parametrize("section", LOAD_BEARING)
def test_no_section_grants_an_exception_to_its_own_rule(section):
    found = hedges_in(_section(section))
    assert not found, f"the '{section}' section grants an exception: {found}"


class TestItWiresIntoTheRest:
    def test_it_points_at_the_asking_rules(self):
        assert "references/asking.md" in _body()

    def test_it_does_not_duplicate_the_property_definitions(self):
        # The contract defines what each property means. A skill restating the
        # definitions is a second copy nothing compares.
        body = _body()
        assert "adapters/README.md" in body
        assert "second shape of the composite step" not in body.lower(), (
            "this is the contract's own wording; point at it instead"
        )
