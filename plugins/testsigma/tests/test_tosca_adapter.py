"""The Tosca subset export adapter, and Element Resolution as its own Phase.

Everything asserted here was established by reading a real export rather than
documentation: 405 entities, no order attribute anywhere, no locator entities at
all, transitively closed, and values written in a small language of their own.

This adapter is also what proves the Phase structure follows the source. For a
page-object source, resolution is part of mapping; here there is nothing in the
source to read, so it is a Phase.
"""

from pathlib import Path

import pytest

from support import (
    ADAPTERS_DIR,
    FIXTURES_DIR,
    REQUIRED_ADAPTER_SECTIONS,
    THREE_PROPERTIES,
    has_paragraph_with,
    hedges_in,
    markdown_sections,
    parse_count_table,
    read_frontmatter,
    skill_files,
)
from tosca import Export

FIXTURE = FIXTURES_DIR / "tosca-subset-export" / "example.tsu"

#: The real export the adapter's numbers were measured from. Customer data, so
#: it lives outside the repository and the checks against it skip when it is
#: absent. The fixture below carries the same shapes and always runs.
REAL_EXPORT = Path("/Users/rahul/temp/CHIPCLIP.tsu")

TOSCA = ADAPTERS_DIR / "tosca-subset-export.md"

LOAD_BEARING = ("sequence", "locators", "values")


def _meta():
    meta, _ = read_frontmatter(TOSCA)
    return meta


def _body():
    _, body = read_frontmatter(TOSCA)
    return body


def _section(needle):
    sections = markdown_sections(_body())
    matching = [v for k, v in sections.items() if needle in k.lower()]
    assert len(matching) == 1, (
        f"expected exactly one section whose heading contains {needle!r}, found "
        f"{len(matching)}. Headings are: {list(sections)}"
    )
    return matching[0]


class TestItIsAValidAdapter:
    def test_it_exists(self):
        assert TOSCA.is_file()

    @pytest.mark.parametrize("prop", THREE_PROPERTIES)
    def test_it_declares_each_of_the_three_properties(self, prop):
        assert prop in _meta(), f"{prop} is not declared"
        assert str(_meta()[prop]) in ("yes", "no", "sometimes")

    @pytest.mark.parametrize("section", REQUIRED_ADAPTER_SECTIONS)
    def test_it_carries_each_required_section(self, section):
        headings = [h.lower() for h in markdown_sections(_body())]
        assert any(section.lower() in h for h in headings), (
            f"no section for {section}; headings are {headings}"
        )

    def test_the_three_properties_are_the_ones_the_source_actually_has(self):
        meta = _meta()
        # Control flow is explicit as nodes with branch folders, so nothing
        # hides behind a helper.
        assert meta["hides-sequence"] == "no"
        # Not one locator: no module attribute entities, no identification
        # parameters. Verified against the real export.
        assert meta["carries-locators"] == "no"
        # A single value can encode several actions.
        assert meta["value-language"] == "yes"

    def test_it_covers_the_opposite_corner_from_the_cucumber_adapter(self):
        # The two shipping adapters differ on all three properties, which is
        # why a third is not needed for coverage.
        cucumber, _ = read_frontmatter(ADAPTERS_DIR / "cucumber-java.md")
        for prop in THREE_PROPERTIES:
            assert _meta()[prop] != cucumber[prop], (
                f"both adapters declare {prop} the same way; the pair no longer "
                f"covers the property space"
            )


class TestSequenceComesFromAssociationPosition:
    def test_order_is_association_list_position(self):
        # "position" and "association" both recur in the paragraph explaining
        # why walking the entity list is wrong, so co-occurrence passed with
        # the rule replaced by "order follows the entity list".
        assert has_paragraph_with(
            _section("sequence"), "only by position within the association"
        )

    def test_it_says_no_entity_carries_an_order(self):
        # "contain no such field" kept "no", "order" and "attribute" in the
        # paragraph after the rule was inverted to "each entity carries its
        # order".
        assert has_paragraph_with(
            _section("sequence"), "no entity has", "order"
        ), "a reader needs to know there is nothing to sort by"

    def test_walking_the_entity_list_is_named_as_wrong(self):
        assert has_paragraph_with(
            _section("sequence"),
            "entity list",
            absent=("walk the entity list in file order,",),
        )

    def test_reusable_blocks_are_resolved_to_recover_true_sequence(self):
        section = _section("sequence")
        assert "reuseabletestblock" in section.lower().replace(" ", "") or (
            "reusable" in section.lower()
        )
        assert has_paragraph_with(section, "transitively closed", "recover")

    def test_resolution_carries_a_visited_set(self):
        # Found the hard way: the entity graph is not a tree, and following
        # references without one recurses until the interpreter gives up.
        assert has_paragraph_with(
            _section("sequence"), "visited", "cycle"
        ), "the graph cycles; resolution without a visited set does not terminate"


class TestItCarriesNoLocators:
    def test_the_absence_is_stated_as_a_finding(self):
        assert has_paragraph_with(_section("locators"), "no locators")

    def test_it_names_what_is_absent_rather_than_only_saying_none(self):
        # "No locators" is checkable only if you know what would have carried
        # them.
        assert "xmoduleattribute" in _section("locators").lower().replace(" ", "")

    def test_element_resolution_is_its_own_phase_here(self):
        assert has_paragraph_with(
            _section("locators"),
            "phase of its own",
            absent=("part of mapping for this source",),
        )

    def test_the_absence_is_reported_rather_than_silently_producing_none(self):
        assert has_paragraph_with(_section("locators"), "report")

    def test_element_names_are_carried_forward_for_the_phase_to_satisfy(self):
        assert has_paragraph_with(_section("locators"), "step map", "carried forward")


class TestValuesAreASmallLanguage:
    def test_a_value_can_encode_a_sequence_of_actions(self):
        assert has_paragraph_with(_section("values"), "sequence", "one value")

    def test_it_says_there_is_no_helper_to_open(self):
        # The second shape of the Composite Step problem: the sequence is inside
        # a value, so there is no file to go and read.
        assert has_paragraph_with(_section("values"), "no helper")

    def test_a_wildcard_value_raises_a_question(self):
        assert has_paragraph_with(
            _section("values"),
            "wildcard",
            "question",
            absent=("write a wildcard comparison",),
        )

    def test_the_token_normalisation_rule_is_stated(self):
        # Review caught this: the 13-token and CLICK-at-47 figures only hold
        # under case-folding and argument-stripping, and the export really does
        # spell the same action `{Click}` 43 times and `{CLICK}` 4 times. A
        # count with an unstated normalisation is not reproducible.
        section = _section("values")
        assert has_paragraph_with(section, "normalise a token", "bracketed argument")
        assert has_paragraph_with(section, "17 literal", "13 action names")

    def test_it_gives_the_measured_share_of_wildcard_values(self):
        # 41 of 215 values in the real export. A rule with no magnitude gets
        # planned around as an edge case.
        assert "41" in _section("values")


class TestEnumeration:
    def test_it_states_what_makes_two_steps_the_same_source_step(self):
        assert has_paragraph_with(_section("enumeration"), "same source step")

    def test_it_carries_a_worked_example_from_the_real_export(self):
        section = _section("enumeration")
        for number in ("48", "19", "2.53"):
            assert number in section, f"the worked example is missing {number}"

    def test_a_data_driven_test_is_a_template_plus_instances(self):
        assert has_paragraph_with(
            _section("enumeration"),
            "template",
            "instance",
            absent=("migrate the instances",),
        ), "migrating instances rather than the template yields N duplicated tests"


@pytest.mark.parametrize("section", LOAD_BEARING)
def test_no_section_grants_an_exception_to_its_own_rule(section):
    found = hedges_in(_section(section))
    assert not found, f"the '{section}' section grants an exception: {found}"


class TestTheResolveElementsSkill:
    SKILL = None

    def _skill(self):
        matches = [s for s in skill_files() if s.parent.name == "resolve-elements"]
        assert len(matches) == 1, "there is no resolve-elements skill"
        return matches[0]

    def _text(self):
        _, body = read_frontmatter(self._skill())
        return body

    def test_it_exists(self):
        assert self._skill().is_file()

    def test_it_runs_only_where_the_source_carries_no_locators(self):
        assert has_paragraph_with(self._text(), "carries-locators", "no")

    def test_it_runs_after_mapping_rather_than_inside_it(self):
        assert has_paragraph_with(self._text(), "after mapping")

    def test_it_takes_the_element_names_the_step_map_references(self):
        assert has_paragraph_with(self._text(), "step map", "element")

    def test_it_reuses_existing_screens_by_name_before_creating_any(self):
        assert has_paragraph_with(self._text(), "by name", "before")

    def test_operator_capture_is_the_last_resort(self):
        assert has_paragraph_with(self._text(), "capture", "only when")

    def test_an_unresolved_element_becomes_residue_and_blocks_assembly(self):
        text = self._text()
        assert has_paragraph_with(text, "residue.md", "unresolved element")
        assert has_paragraph_with(text, "block", "placeholder")

    def test_it_writes_the_marker_that_says_the_phase_is_done(self):
        # migration-directory.md and resume.md both depend on migration.md
        # gaining an Element Resolution section, and its absence meaning the
        # Phase is open. Nothing wrote it, so a completed Phase read as
        # unfinished forever.
        assert has_paragraph_with(
            self._text(), "element resolution", "migration.md", "absence"
        ), "the Phase must write the marker a later session reads"

    def test_it_points_at_the_shared_references(self):
        text = self._text()
        assert "references/migration-directory.md" in text
        assert "references/asking.md" in text


# --- the rules, applied to a fixture ------------------------------------------

class TestTheAdaptersRulesAgainstAFixture:
    """The adapter's rules, executed. `tosca.py` transcribes them; this checks
    the transcription against a fixture carrying every trap the real export
    showed: a cycle, a module name ending in a space, one containing a pipe, a
    value spelling an action two ways, a multi-action value, a wildcard value,
    an orphan step, and a template with instances.
    """

    @pytest.fixture(scope="class")
    @classmethod
    def export(cls):
        return Export.load(FIXTURE)

    def test_the_fixture_is_transitively_closed(self, export):
        assert export.dangling() == set()

    def test_the_entity_graph_cycles(self, export):
        # Not defensive: this is why the adapter requires a visited set.
        assert export.cycles(), "the fixture no longer exercises the cycle"

    def test_sequence_comes_from_association_position_not_file_order(self, export):
        test_case = export.of_class("TestCase")[0]
        recovered = export.sequence(test_case)
        file_order = [
            e["Surrogate"] for e in export.entities
            if e["ObjectClass"] == "XTestStep" and e["Surrogate"] in set(recovered)
        ]
        assert recovered == ["s-search", "s-open", "s-search-2", "s-verify"]
        assert recovered != file_order, (
            "the fixture must differ between recovered and file order, or it "
            "proves nothing about which one is right"
        )

    def test_a_reusable_block_is_spliced_in_at_the_references_position(self, export):
        # The reference itself contributes no step.
        assert "ref1" not in export.sequence(export.of_class("TestCase")[0])

    def test_an_orphan_step_is_reachable_from_no_test_case(self, export):
        assert export.orphan_steps() == ["s-orphan"]

    def test_two_uses_of_one_module_are_one_source_step(self, export):
        counts = export.source_steps()
        assert counts["Org Search | Fixture"] == 2
        assert len(counts) == 3

    def test_a_module_name_may_end_in_a_space_or_contain_a_pipe(self, export):
        names = list(export.source_steps())
        assert any(n.endswith(" ") for n in names)
        assert any("|" in n for n in names)

    def test_token_normalisation_merges_two_spellings_of_one_action(self, export):
        # The rule the adapter now states, and the reason it needs to.
        assert len(export.literal_tokens()) == 5
        assert export.action_names()["CLICK"] == 3

    def test_a_value_can_hold_a_sequence_of_actions(self, export):
        assert export.multi_action_values() == ["{CLICK}{DOWN}{ENTER}"]

    def test_a_wildcard_value_is_found_rather_than_read_as_an_action(self, export):
        assert export.wildcard_values() == ["*Inventory for Test ID AB123*"]

    def test_a_template_carries_its_instances(self, export):
        detail = export.of_class("TestCaseTemplateDetail")[0]
        assert len(detail["Assocs"]["Instances"]) == 2


# --- the stated numbers, against the real export ------------------------------

@pytest.mark.skipif(not REAL_EXPORT.exists(), reason="the real export is not on this machine")
class TestTheStatedNumbersAgainstTheRealExport:
    """Acceptance criterion 8, executed rather than asserted.

    Every number in the adapter was measured from this file. Without this the
    criterion rested on arithmetic done once by hand, and the numbers could
    drift on any later edit with nothing noticing.
    """

    @pytest.fixture(scope="class")
    @classmethod
    def export(cls):
        return Export.load(REAL_EXPORT)

    def test_the_structural_claims_hold(self, export):
        assert len(export.entities) == 405
        assert len(export.attribute_names()) == 46
        assert export.dangling() == set()
        assert export.of_class("XModuleAttribute") == [], "this source carries no locators"
        assert export.cycles()

    def test_nothing_carries_an_order(self, export):
        names = export.attribute_names()
        assert not [n for n in names if n.lower().startswith(("order", "index", "sequence", "position"))]
        assert "ReorderAllowed" in names, "a permission, not a position"

    def test_the_enumeration_numbers_hold(self, export):
        counts = export.source_steps()
        assert sum(counts.values()) == 48
        assert len(counts) == 19
        assert export.collapse_ratio() == 2.53
        assert sum(1 for v in counts.values() if v == 1) == 4
        assert len(export.orphan_steps()) == 8

    def test_the_value_numbers_hold(self, export):
        assert len(export.values()) == 215
        assert all(export.values())
        assert len(export.literal_tokens()) == 17
        assert len(export.action_names()) == 13
        assert export.action_names()["MOUSEOVER"] == 53
        assert export.action_names()["CLICK"] == 47
        assert len(export.multi_action_values()) == 2
        assert len(export.wildcard_values()) == 41

    def test_the_worked_example_table_matches_the_export(self, export):
        # One row per distinct Source Step, as adapters/README.md requires. It
        # listed only the top eight until review pointed out that a partial
        # table cannot be checked against the rule that produced it.
        stated = parse_count_table(_section("enumeration"))
        counts = {str(k).strip(): v for k, v in export.source_steps().items()}
        assert stated, "the worked example table did not parse"
        assert {k.strip(): v for k, v in stated.items()} == counts, (
            "the stated table and the export disagree"
        )
        assert sum(stated.values()) == 48 and len(stated) == 19

    def test_only_one_test_case_is_populated_so_the_hedge_is_accurate(self, export):
        # The adapter says file order agreeing here is a coincidence of this
        # file rather than a property. That hedge depends on there being one
        # populated test case, so it is checked rather than assumed.
        assert len(export.populated_test_cases()) == 1
