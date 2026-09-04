"""The assembly skill: tests built from reviewed rows, checked for order.

ADR-0005 puts the order-and-nesting check inside this stage rather than in a
verification skill, and ADR-0001 makes it a property of a whole test rather than
of a step, because it describes a fault that only exists between steps.
"""

import re

import pytest

from support import (
    PLUGIN_ROOT,
    has_paragraph_with,
    hedges_in,
    markdown_sections,
    read_frontmatter,
)

ASSEMBLE = PLUGIN_ROOT / "skills" / "assemble" / "SKILL.md"
SCRIPT = PLUGIN_ROOT / "scripts" / "check_step_order.py"

LOAD_BEARING = ("reviewed", "unresolved element", "nesting", "sweep", "out of place")


def _body():
    _, body = read_frontmatter(ASSEMBLE)
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
        assert ASSEMBLE.is_file()

    def test_its_description_says_it_assembles_tests(self):
        meta, _ = read_frontmatter(ASSEMBLE)
        description = str(meta.get("description", "")).lower()
        assert "assemble" in description or "assembly" in description
        assert "step map" in description


class TestOnlyReviewedRowsReachATest:
    def test_an_unreviewed_row_cannot_be_assembled(self):
        assert has_paragraph_with(
            _section("reviewed"),
            "unreviewed",
            "never",
            absent=("if time is short",),
        ), "an unreviewed mapping must not reach a finished test"

    def test_it_says_where_the_row_status_comes_from(self):
        assert "step-map.md" in _section("reviewed")


class TestAnUnresolvedElementRefusesTheTest:
    def test_the_test_is_refused_rather_than_placeheld(self):
        assert has_paragraph_with(
            _section("unresolved element"),
            "refuse",
            "placeholder",
            absent=("assemble it anyway",),
        )

    def test_it_reads_the_block_at_the_elements_granularity(self):
        # residue.md is keyed by Source Step and element precisely so this
        # decision can be made per element rather than per row.
        section = _section("unresolved element")
        assert "residue.md" in section
        assert has_paragraph_with(section, "element", "parameter value")


class TestTheOrderCheck:
    def test_it_is_the_exit_condition_of_this_stage(self):
        assert has_paragraph_with(_section("nesting"), "exit condition")

    def test_it_runs_against_a_whole_test(self):
        assert has_paragraph_with(
            _section("nesting"),
            "whole test",
            absent=("per step", "each step alone"),
        ), "the fault only exists between steps, so a single step cannot carry it"

    def test_the_property_is_computed_here_and_not_delegated_to_the_cli(self):
        assert has_paragraph_with(
            _section("nesting"),
            "cli",
            absent=("delegate", "let the cli", "rely on the cli"),
        ), "the check must hold whatever the installed build happens to verify"

    def test_it_names_the_script_that_computes_it(self):
        assert "check_step_order.py" in _body()
        assert SCRIPT.is_file(), "the skill names a script that does not exist"

    def test_it_states_the_property_arithmetically(self):
        section = _section("nesting")
        assert has_paragraph_with(section, "parent", "next sibling")
        # Without this clause the property is wrong for a last child, which has
        # no next sibling and so no upper bound at all.
        assert has_paragraph_with(section, "no upper bound", "no next sibling")

    def test_it_says_an_id_is_not_an_order(self):
        # The correction measured on real data: ids are assigned at creation, so
        # a step authored later carries a higher id while sitting earlier.
        assert has_paragraph_with(_section("nesting"), "id", "not the order")

    def test_it_says_why_a_round_trip_cannot_find_this(self):
        assert has_paragraph_with(_section("nesting"), "round trip", "parentage")


class TestReportingAFailure:
    def test_the_specific_steps_are_named(self):
        assert has_paragraph_with(
            _section("out of place"),
            "which steps",
            absent=("that the test is wrong",),
        ) or has_paragraph_with(_section("out of place"), "each step", "window")

    def test_a_step_with_no_reported_order_is_not_a_pass(self):
        assert has_paragraph_with(_section("out of place"), "not checked")


@pytest.mark.parametrize("section", LOAD_BEARING)
def test_no_section_grants_an_exception_to_its_own_rule(section):
    found = hedges_in(_section(section))
    assert not found, f"the '{section}' section grants an exception to its own rule: {found}"


class TestItWiresIntoTheRest:
    def test_it_points_at_the_migration_directory_definition(self):
        assert "references/migration-directory.md" in _body()

    def test_it_points_at_the_asking_rules(self):
        assert "references/asking.md" in _body()

    def test_it_records_the_check_it_ran(self):
        assert "check-record.md" in _body()

    def test_no_step_ordering_detail_is_duplicated_from_the_script(self):
        # The arithmetic has one implementation. A skill restating it is a
        # second copy with nothing comparing them.
        assert "pre-order" not in _body().lower() or "check_step_order.py" in _body()


class TestTheUnreferencedElementSweep:
    """A cheap check the verification pass ran and that found a real dropped step.

    46 elements, two unreferenced, one of them a locator that had been lifted
    correctly while the step using it was never written. Nothing else in the
    converted test pointed at the gap.
    """

    def test_the_sweep_exists(self):
        assert has_paragraph_with(_section("sweep"), "element", "no step")

    def test_an_unreferenced_element_is_read_as_a_dropped_step(self):
        assert has_paragraph_with(_section("sweep"), "dropped step")

    def test_the_benign_case_is_distinguished_from_the_fault(self):
        # An element for a scenario nobody has converted yet is not a fault.
        assert has_paragraph_with(
            _section("sweep"), "benign", "converted"
        ), "reporting every unreferenced element as a fault makes the sweep noise"

    def test_a_missing_step_sends_its_row_back_to_unreviewed(self):
        assert has_paragraph_with(_section("sweep"), "unreviewed")

    def test_the_sweeps_coverage_is_stated_rather_than_implied(self):
        # It finds a dropped step only where an element was left behind. A step
        # that captured a value rather than touching the screen leaves nothing
        # for it to notice, so a clean sweep is not evidence of no omission.
        assert has_paragraph_with(
            self_section := _section("sweep"), "only finds", "element behind"
        )
        assert has_paragraph_with(
            self_section, "clean sweep", "no step was dropped"
        ), "a clean sweep must not be reported as proof"

    def test_the_ratio_says_whether_the_omission_was_systematic(self):
        assert has_paragraph_with(
            _section("sweep"), "isolated", "systematic"
        ), "one missing step and a pattern of them need different responses"
