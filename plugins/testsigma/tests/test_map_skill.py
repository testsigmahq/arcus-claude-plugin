"""The mapping skill: the Step Map, compare-to-source, and Residue.

The core of the plugin, and the stage that owns the check ADR-0001 puts second
and ADR-0005 refuses to give a skill of its own. Four of the six known faults
were a source line hiding a helper that did something else, so most of what is
asserted here is that the skill requires opening that helper and requires the
comparison before a row can be called finished.
"""

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
LOAD_BEARING = ("one distinct source step", "helper", "compare", "residue")


def _body():
    _, body = read_frontmatter(MAP)
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
