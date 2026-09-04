"""The mapping skill: the Step Map, compare-to-source, and Residue.

The core of the plugin, and the stage that owns the check ADR-0001 puts second
and ADR-0005 refuses to give a skill of its own. Four of the six known faults
were a source line hiding a helper that did something else, so most of what is
asserted here is that the skill requires opening that helper and requires the
comparison before a row can be called finished.
"""

import re

import pytest

from support import (
    PLUGIN_ROOT,
    has_paragraph_with,
    hedges_in,
    markdown_sections,
    read_frontmatter,
    skill_files,
)

MAP = PLUGIN_ROOT / "skills" / "map" / "SKILL.md"

#: The five things a Step Map row carries, so that reviewing a row does not mean
#: going back to the source.
ROW_COLUMNS = ("source", "occurrence", "parameter", "expression", "status")

#: Every helper name that is treated as a loop until the source proves
#: otherwise. A helper that re-drives the interface looks identical to a passive
#: wait once flattened.
LOOP_NAMES = ("wait", "until", "refresh", "poll")

#: Sections stating absolute rules. A paragraph granting an exception anywhere
#: in one of these guts the rule while leaving its sentence intact.
LOAD_BEARING = ("one distinct source step", "helper", "element", "compare", "residue")


def _body():
    _, body = read_frontmatter(MAP)
    return body


def _sections():
    return markdown_sections(_body())


def _bold_leads(text):
    """The bold lead-ins of a section, in document order.

    The three places an element is looked for are bold-led list items, so their
    order is structural rather than a matter of phrasing. Asserting the order
    this way survives rewording and cannot be satisfied by a coincidence in a
    neighbouring paragraph, which is how three assertions here were defeated.
    """
    return re.findall(r"\*\*(.+?)\*\*", text, re.S)


def _section(needle):
    matching = [v for k, v in _sections().items() if needle in k.lower()]
    assert len(matching) == 1, (
        f"expected exactly one section whose heading contains {needle!r}, found "
        f"{len(matching)}. Headings are: {list(_sections())}"
    )
    return matching[0]


class TestTheSkillExists:
    def test_it_exists(self):
        assert MAP.is_file()

    def test_its_description_says_it_maps_source_steps(self):
        meta, _ = read_frontmatter(MAP)
        description = str(meta.get("description", "")).lower()
        assert "step map" in description or "map" in description
        assert "source step" in description

    def test_no_separate_verification_skill_exists(self):
        # ADR-0005 expressed as a test. A check placed after everything is a
        # check that does not run; it ran once, retroactively, on the one
        # conversion that had one.
        for skill in skill_files():
            name = skill.parent.name
            assert name not in ("verify", "verification", "check", "validate"), (
                f"{name} is a skill whose job is verification; ADR-0005 refuses one"
            )


class TestOneDistinctSourceStepAtATime:
    def test_the_unit_of_work_is_the_distinct_source_step(self):
        assert has_paragraph_with(
            _section("one distinct source step"), "distinct", "occurrence"
        )

    def test_a_verdict_is_reused_at_every_occurrence(self):
        # This is the whole economics of the plugin: cost scales with the
        # suite's vocabulary rather than with its line count.
        assert has_paragraph_with(
            _section("one distinct source step"), "reuse", "every occurrence"
        )

    @pytest.mark.parametrize("column", ROW_COLUMNS)
    def test_a_row_carries_each_of_the_five_things(self, column):
        assert column in _section("what a row carries").lower(), (
            f"a row must carry {column}, so reviewing it does not mean going "
            f"back to the source"
        )

    def test_one_source_step_may_map_to_several_steps(self):
        assert has_paragraph_with(
            _section("what a row carries"),
            "several",
            absent=("exactly one", "must map to one"),
        ), "a source line that really does three things must not be forced into one"


class TestOpeningTheHelper:
    def test_the_helper_behind_the_line_is_opened_every_time(self):
        assert has_paragraph_with(_section("helper"), "open", "every")

    def test_it_is_read_against_the_implementation_not_the_surface(self):
        assert has_paragraph_with(_section("helper"), "implementation", "surface")

    def test_a_helper_doing_less_than_its_line_implies_is_reported(self):
        assert has_paragraph_with(_section("helper"), "less", "implies")

    def test_a_helper_doing_more_than_its_line_implies_is_reported(self):
        assert has_paragraph_with(_section("helper"), "more", "implies")

    @pytest.mark.parametrize("name", LOOP_NAMES)
    def test_each_loop_shaped_helper_name_is_treated_as_a_loop(self, name):
        section = _section("helper").lower()
        assert name in section, f"a helper named {name} must be treated as a loop"

    def test_a_loop_is_the_default_until_the_source_shows_otherwise(self):
        assert has_paragraph_with(
            _section("helper"),
            "loop",
            "until the source",
            absent=("assume it is a wait", "treat it as a wait"),
        ), "a helper that re-drives the interface looks identical to a wait once flattened"

    def test_it_follows_a_helper_that_delegates(self):
        # Stopping at the first method the step definition names is the most
        # natural way to get this wrong, because that method looks complete.
        assert has_paragraph_with(_section("helper"), "delegat", "follow")

    def test_it_points_at_the_adapter_rather_than_restating_the_format(self):
        # The traps are per-format and live in the adapter's Sequence section.
        assert "sequence" in _section("helper").lower()
        assert "adapter" in _section("helper").lower()


class TestOneReadingAsksBothQuestions:
    """Locators and sequence come out of the same files, in one pass.

    This is not an optimisation. On the first conversion all forty-six locators
    came out of the Java page objects, and those were the same files that had to
    be opened for sequence. They were opened for locators, the question of what
    the code actually did was never asked, and that is how four of the six
    faults got through. Separating the two readings is the bug.
    """

    def test_locators_are_read_in_the_same_pass_as_sequence(self):
        assert has_paragraph_with(_section("helper"), "same file", "one reading")

    def test_the_locator_question_is_asked_of_the_helper_section_itself(self):
        # If this instruction migrates to a section of its own, the two readings
        # have been separated again, which is the fault.
        assert "locator" in _section("helper").lower()

    def test_it_says_why_separating_the_readings_is_the_fault(self):
        assert has_paragraph_with(_section("helper"), "separat", "reading")


class TestResolvingAnElement:
    def test_the_three_places_are_tried_in_order(self):
        # Structural. "source" and "first" co-occur in the capture paragraph too
        # ("their time is the last resort and not the first"), which passed this
        # with the source demoted to "one option among three".
        leads = _bold_leads(_section("element"))
        found = {}
        for index, lead in enumerate(leads):
            for place in ("source", "existing", "capture"):
                if place in lead.lower() and place not in found:
                    found[place] = index
        assert set(found) == {"source", "existing", "capture"}, (
            f"the three places an element comes from are not all named: {leads}"
        )
        assert found["source"] < found["existing"] < found["capture"], (
            f"the three places are out of order: {leads}"
        )
        assert "first" in leads[found["source"]].lower(), (
            "the source must be named as the first place tried, not merely as one of them"
        )

    def test_it_stops_at_the_first_place_that_answers(self):
        assert has_paragraph_with(_section("element"), "stop at the first")

    def test_existing_screens_are_reused_by_name_before_anything_is_created(self):
        assert has_paragraph_with(
            _section("element"),
            "by name",
            "before",
            absent=("after creating",),
        ), "a Migration must not duplicate screens the Operator already maintains"

    def test_operator_capture_happens_only_when_nothing_else_can_supply_it(self):
        # "last resort" appears twice in this section, so the old assertion
        # passed with the condition on asking deleted.
        assert has_paragraph_with(
            _section("element"), "capture", "only when", "neither"
        ), "the Operator's time must be the last resort, not the first"

    def test_an_unresolved_element_becomes_residue_with_that_cause(self):
        # Paragraph-scoped: "distinct" also appears in the estimation
        # paragraph ("108 distinct control-and-screen pairs"), which passed this
        # with the two causes explicitly merged.
        assert has_paragraph_with(
            _section("element"), "residue.md", "unresolved element", "distinct"
        ), "an unresolved element and an unexpressible step are distinct causes"

    def test_an_unresolved_element_blocks_assembly_rather_than_placeholding(self):
        # A test that looks finished and cannot run is worse than an absent one.
        assert has_paragraph_with(
            _section("element"),
            "block",
            "placeholder",
            absent=("assemble it anyway",),
        )

    def test_it_runs_here_only_where_the_source_carries_locators(self):
        # Whether this is a Phase of its own is a property of the source, not of
        # the Migration.
        assert has_paragraph_with(_section("element"), "carries-locators", "phase")

    def test_the_block_is_recorded_at_the_elements_granularity(self):
        # A generic step can carry far more parameter values than rows, so
        # marking the whole row residue would block every occurrence that
        # resolved perfectly well. Review found this stated as an absolute rule
        # with no data model able to express it.
        assert has_paragraph_with(
            _section("element"), "granularity", "parameter value"
        ), "an unresolved element must not block the occurrences that resolved"

    def test_the_format_specific_measurement_stays_in_the_adapter(self):
        # The adapter is the only part of a Migration that knows the format.
        # A measured figure copied into this skill is a second copy that can
        # drift, and nothing would compare them.
        body = _body()
        assert "108" not in body, (
            "a format-specific measurement belongs in the adapter's own section"
        )
        assert "locators section" in body.lower(), (
            "point at the adapter's measurement rather than restating it"
        )

    def test_element_count_is_not_estimated_from_the_step_count(self):
        # One generic step occurring hundreds of times still names hundreds of
        # different things to find. A measured suite had 108 control-and-screen
        # pairs behind a single Source Step.
        assert has_paragraph_with(
            _section("element"), "distinct", "parameter values"
        ), "estimating element work as a proportion of Source Steps is badly wrong"


class TestTheComparisonGatesTheRow:
    def test_a_row_cannot_be_finished_before_the_comparison_has_run(self):
        assert has_paragraph_with(
            _section("compare"),
            "cannot",
            "reviewed",
            absent=("unless time", "if there is time"),
        ), "the comparison must gate the row, or it becomes the check that never runs"

    def test_the_comparison_is_the_exit_condition_of_the_stage(self):
        assert has_paragraph_with(_section("compare"), "exit condition")

    def test_it_says_why_running_the_test_cannot_replace_the_comparison(self):
        # Every fault in the class produces a test that runs and passes.
        assert has_paragraph_with(_section("compare"), "runs and passes")

    def test_a_weak_comparison_in_the_source_raises_a_question(self):
        assert has_paragraph_with(
            _section("compare"),
            "wildcard",
            "question",
            "unreviewed",
        ), "a weak assertion in the source is not licence to write a weak one"

    def test_the_weak_comparison_rule_covers_substring_too(self):
        assert "substring" in _section("compare").lower()


class TestResidue:
    def test_an_entry_carries_a_cause(self):
        assert has_paragraph_with(_section("residue"), "cause")

    def test_an_entry_carries_the_reasoning_that_produced_it(self):
        assert has_paragraph_with(_section("residue"), "reasoning")

    def test_an_entry_can_be_reopened(self):
        # One case already believed unexpressible turned out to have a spelling
        # nobody had found.
        assert has_paragraph_with(_section("residue"), "overturn", "revisited")

    def test_residue_is_distinguished_from_divergence(self):
        # One is work declined, the other work done wrongly and reported as done.
        assert "divergence" in _section("residue").lower()


@pytest.mark.parametrize("section", LOAD_BEARING)
def test_no_section_grants_an_exception_to_its_own_rule(section):
    found = hedges_in(_section(section))
    assert not found, f"the '{section}' section grants an exception to its own rule: {found}"


class TestItWiresIntoTheRest:
    def test_it_points_at_the_migration_directory_definition(self):
        assert "references/migration-directory.md" in _body()

    def test_it_points_at_the_asking_rules(self):
        assert "references/asking.md" in _body()

    def test_it_refuses_to_map_before_a_migration_exists(self):
        assert has_paragraph_with(
            _body(), ".testsigma/migration/", "survey"
        ), "there is nothing to map into before survey has run"
