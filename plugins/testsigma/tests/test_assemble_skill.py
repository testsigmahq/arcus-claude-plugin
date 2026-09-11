"""The assembly skill: tests built from reviewed rows, checked for order.

ADR-0005 puts the order-and-nesting check inside this stage rather than in a
verification skill, and ADR-0001 makes it a property of a whole test rather than
of a step, because it describes a fault that only exists between steps.
"""

import pytest

from support import (
    document,
    PLUGIN_ROOT,
    has_paragraph_with,
    hedges_in,
    read_frontmatter,
)

ASSEMBLE = PLUGIN_ROOT / "skills" / "assemble" / "SKILL.md"

DOC = document(ASSEMBLE)


def _body():
    return DOC.body


def _section(needle):
    return DOC.section(needle)

SCRIPT = PLUGIN_ROOT / "scripts" / "check_step_order.py"

LOAD_BEARING = ("reviewed", "unresolved element", "nesting", "sweep", "out of place")


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
    def test_the_test_is_refused_and_the_reason_is_deferred_to(self):
        # It used to restate why refusing beats placeholding, in the same words
        # as references/element-resolution.md and skills/resolve-elements.
        # Three copies of one safety rule is two that can soften unnoticed, so
        # the rule moved to the reference and this asserts the refusal plus the
        # deferral rather than the prose.
        section = _section("unresolved element")
        assert has_paragraph_with(section, "refuse", absent=("assemble it anyway",))
        assert "references/element-resolution.md" in section, (
            "the refusal must point at what owns the reason for it"
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
        # The clause this test used to pin was wrong, and pinning it kept the
        # script wrong too: "no upper bound where the parent has no next
        # sibling" gives a step whose parent is an only child no bound at all,
        # so at three levels deep the primary fault class went unreported. The
        # bound comes from the nearest *ancestor* that has a next sibling.
        assert has_paragraph_with(section, "ancestor", "next sibling"), (
            "the upper bound is not the direct parent's next sibling"
        )
        assert has_paragraph_with(section, "no upper bound", "no ancestor"), (
            "and there is no bound only when no ancestor has one at all"
        )

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

    def test_the_sweep_is_named_as_secondary_to_call_chain_coverage(self):
        # Measured: three element audits found one defect between them and
        # produced two false positives; composites converted partway accounted
        # for six. The sweep is worth running and is not the primary check.
        assert has_paragraph_with(
            _section("sweep"), "secondary", "call-chain coverage"
        )
        assert has_paragraph_with(
            _section("sweep"), "do not mistake it for the check"
        ), "presenting a sweep as the primary check misplaces the effort"

    def test_an_unreferenced_element_is_read_as_a_dropped_step(self):
        assert has_paragraph_with(_section("sweep"), "dropped step")

    def test_the_benign_case_is_distinguished_from_the_fault(self):
        # An element for a scenario nobody has converted yet is not a fault.
        assert has_paragraph_with(
            _section("sweep"), "benign", "converted"
        ), "reporting every unreferenced element as a fault makes the sweep noise"

    def test_a_missing_step_sends_its_row_back_to_unreviewed(self):
        assert has_paragraph_with(_section("sweep"), "unreviewed")

    def test_the_total_is_re_derived_rather_than_quoted(self):
        # The measured pass quoted 46 elements for a dozen steps; the real
        # total was 42. This skill quoted it too, from the same stale source.
        assert has_paragraph_with(
            _section("sweep"), "re-derive the total", "quoting an earlier"
        )

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


class TestAResidueRowBecomesAMarker:
    """A declined step must still be visible in the test it was declined from.

    This is the seam where Residue turns into a Divergence if it is got wrong.
    Mapping decides a step is inexpressible; if assembly then treats `residue`
    as merely "not `reviewed`" and skips the row, the test reads as a complete
    conversion of its source and is not. Nothing downstream catches it: the file
    validates, pushes, round-trips, and the only record of the absence is in a
    directory the person running the test never opens.
    """

    def test_the_stage_has_a_step_for_it(self):
        assert _section("marker"), (
            "assembly must say what becomes of a residue row, or the natural "
            "reading of 'take only reviewed rows' drops it"
        )

    def test_the_marker_stands_where_the_step_would_have_been(self):
        section = _section("marker")
        assert "position" in section, (
            "a marker collected elsewhere loses the sequence position that is "
            "the reason for putting it in the test at all"
        )

    def test_a_residue_row_is_named_as_the_exception_to_the_reviewed_rule(self):
        # Scoped to the reviewed-rows section deliberately. Stating the
        # exception three sections later does not reach a reader who has
        # already applied the rule and moved on.
        assert "residue" in _section("reviewed"), (
            "the rule that drops the row and the exception to it must sit "
            "together"
        )

    def test_it_defers_how_to_write_the_marker_rather_than_restating_it(self):
        assert "authoring.md" in _section("marker"), (
            "the marker's spelling belongs to authoring.md; a second copy here "
            "is one that softens"
        )

    def test_the_per_test_document_is_written_here(self):
        section = _section("marker")
        assert "residue/" in section, (
            "the per-test document can only be written where a test exists, "
            "which is this stage"
        )

    def test_a_test_carrying_markers_is_still_checked(self):
        section = _section("marker")
        assert "refused" in section, (
            "a marker is a recorded absence, not a reason to abandon the test; "
            "say so, or it reads like the unresolved-element refusal above it"
        )
