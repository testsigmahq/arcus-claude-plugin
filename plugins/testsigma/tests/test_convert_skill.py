"""The convert skill: one Conversion, end to end, and then stop.

ADR-0012 makes a Conversion the unit a Migration delivers in. This skill owns
the queue, the ordering and what happens when a Conversion ends; the reading and
building inside it belong to `map` and `assemble`, which it calls rather than
absorbs.

The one-and-stop rule is the load-bearing one. It reads like a preference and is
not: a loop puts the tenth scenario's judgement calls behind nine others' source
reading, and every fault class in this plugin is a judgement failing quietly.
"""

from support import (
    CONTEXT,
    document,
    PLUGIN_ROOT,
    has_paragraph_with,
    hedges_in,
    read_frontmatter,
)

CONVERT = PLUGIN_ROOT / "skills" / "convert" / "SKILL.md"

DOC = document(CONVERT)


def _body():
    return DOC.body


def _flat():
    return DOC.flat


class TestTheSkillExists:
    def test_it_exists(self):
        assert CONVERT.is_file(), "a Migration has no way to deliver a test"

    def test_its_description_says_it_converts_a_scenario(self):
        meta, _ = read_frontmatter(CONVERT)
        description = str(meta.get("description", "")).lower()
        assert "convert" in description
        assert "scenario" in description

    def test_its_description_does_not_advertise_it_as_the_way_into_a_migration(self):
        # Survey is. A description that reads as an entry point gets invoked on
        # a suite with no adapter chosen and no snapshot pinned.
        meta, _ = read_frontmatter(CONVERT)
        description = str(meta.get("description", "")).lower()
        assert "not the way into a migration" in description
        assert "survey" in description

    def test_its_description_says_it_does_one_and_stops(self):
        # The description is what a request is matched against, so "convert the
        # suite" must not read as something this does.
        meta, _ = read_frontmatter(CONVERT)
        description = str(meta.get("description", "")).lower()
        assert "one conversion" in description and "stop" in description


class TestItPerformsOneConversionAndStops:
    def test_the_rule_is_stated_as_binding_rather_than_preferred(self):
        assert has_paragraph_with(
            _body(),
            "exactly one conversion",
            absent=("where possible", "prefer", "generally", "unless the operator asks"),
        ), "one-and-stop must be a rule, not a default the next scenario overrides"

    def test_it_forbids_taking_the_next_scenario(self):
        assert has_paragraph_with(
            _body(), "do not take the next scenario", "do not offer"
        ), "offering to continue is how a loop starts"

    def test_it_gives_the_measured_reason(self):
        # Without the reason the rule reads as arbitrary caution and is the
        # first thing a later edit relaxes.
        assert has_paragraph_with(_body(), "context window", "judgement")

    def test_it_says_a_session_starts_from_the_migration_directory(self):
        assert has_paragraph_with(
            _body(), "migration directory", "previous session"
        ), "a Conversion needing the last session's context makes the directory a decoration"


class TestItRefusesWhereNothingWasSurveyed:
    def test_an_absent_migration_directory_stops_it(self):
        assert has_paragraph_with(
            _body(),
            ".testsigma/migration/",
            "survey has not run",
            "stop",
            absent=("proceed anyway", "create it", "start one"),
        )

    def test_it_reads_the_directory_before_working(self):
        assert has_paragraph_with(_body(), "read it before working", "scenarios.md")


class TestItDelegatesRatherThanRestates:
    def test_it_takes_the_next_scenario_from_the_selection_script(self):
        # Two sessions reading the same state must choose the same scenario.
        assert "scripts/next_conversion.py" in _flat()
        assert has_paragraph_with(
            _body(), "next_conversion.py", "--suite"
        ), "the script needs the suite it is ordering"

    def test_it_forbids_re_deriving_the_choice(self):
        assert has_paragraph_with(
            _body(), "do not re-derive", "do not override"
        ), "a re-derived choice is the non-determinism the script exists to remove"

    def test_the_operator_may_name_a_scenario_once_vocabulary_has_saturated(self):
        assert has_paragraph_with(_body(), "saturated", "operator")

    def test_it_calls_the_mapping_skill(self):
        assert has_paragraph_with(_body(), "`map` skill", "scoped to this scenario")

    def test_it_calls_the_assembly_skill(self):
        assert has_paragraph_with(_body(), "`assemble` skill")

    def test_it_calls_element_resolution_rather_than_restating_it(self):
        assert has_paragraph_with(_body(), "`resolve-elements` skill", "screen")

    def test_the_three_places_are_named_with_the_operator_last(self):
        # Which of the first two is tried first is the reference's rule and is
        # asserted there; what a Conversion owes is that the Operator comes
        # after the project, since a project consulted after them is a project
        # never consulted.
        step = DOC.section("Resolve the elements")
        assert has_paragraph_with(
            step, "the source, the target project and the operator"
        ), "all three places must be named where the Conversion reaches them"
        assert has_paragraph_with(
            step,
            "target project is consulted before the operator",
            absent=("ask the operator first",),
        ), "the Operator must be the last place an element is looked for"

    def test_it_parks_on_elements_only_when_all_three_are_exhausted(self):
        assert has_paragraph_with(
            DOC.section("Resolve the elements"),
            "all three",
            "park",
            absent=("whenever an element is missing",),
        ), "parking before the project is consulted spends the Operator's time first"

    def test_the_whole_screen_goes_to_the_operator_and_not_the_one_element(self):
        assert has_paragraph_with(
            DOC.section("Resolve the elements"), "whole screen", "visit"
        )

    def test_it_does_not_restate_the_check_order(self):
        # `checks.md` fixes it. A second copy here is a copy that drifts.
        assert "references/checks.md" in _flat()
        assert has_paragraph_with(_body(), "do not restate", "shortcut")


class TestDeliveringSoonerWeakensNoCheck:
    def test_the_helper_is_still_opened_before_a_row_is_reviewed(self):
        # The whole risk of delivering sooner is that the reading gets thinner.
        assert has_paragraph_with(
            _body(),
            "helper",
            "opened",
            "compared",
            "reviewed",
            absent=("only for rows that occur often", "skip the comparison"),
        )

    def test_it_says_a_reviewed_row_is_trusted_forever(self):
        assert has_paragraph_with(_body(), "trusted forever", "reused")

    def test_a_reused_row_is_reused_rather_than_re_decided(self):
        assert has_paragraph_with(_body(), "`reviewed` or `adopted`", "reused")

    def test_a_residue_row_does_not_stop_the_conversion(self):
        assert has_paragraph_with(
            _body(), "residue", "marker", absent=("stops the conversion",)
        )


class TestItRecordsWhatTheConversionConsumed:
    def test_it_writes_the_assembled_row_with_the_versions(self):
        assert has_paragraph_with(
            _body(), "`assembled.md`", "row versions", "consumed"
        )

    def test_it_says_why_the_versions_are_what_is_recorded(self):
        # A recorded version behind the row's current one is the whole signal.
        assert has_paragraph_with(_body(), "versions", "working copy")

    def test_it_sets_the_scenario_to_done(self):
        assert has_paragraph_with(_body(), "`scenarios.md`", "`done`")

    def test_it_commits_the_working_copy_and_not_only_the_directory(self):
        # Scoping the commit to the Migration Directory leaves the .sigma file
        # behind, which is half of what the Conversion produced.
        assert has_paragraph_with(
            _body(), "working copy", "migration directory", "commit"
        )
        assert "scripts/check_committed.py" in _flat()

    def test_committing_per_conversion_is_given_its_reason(self):
        assert has_paragraph_with(_body(), "session that ends early")


class TestTheReport:
    def _report(self):
        return DOC.section("Report")

    def test_it_leads_with_the_test_delivered(self):
        report = self._report().lower()
        assert report.index("the test delivered") < report.index("of total scenarios")

    def test_tests_delivered_precedes_rows_reviewed(self):
        # The first is the number the customer counts; the second explains the
        # cost curve. Reversed, the Operator leads with a number the customer
        # cannot act on.
        report = self._report().lower()
        assert report.index("of total scenarios") < report.index("of total distinct")

    def test_it_reports_rows_new_versus_reused(self):
        assert "new versus reused" in self._report().lower()

    def test_it_reports_any_concession_or_residue(self):
        report = self._report().lower()
        assert "concession" in report and "residue" in report

    def test_it_stops_after_reporting(self):
        assert has_paragraph_with(self._report(), "then stop")

    def test_it_carries_none_of_the_four_forbidden_kinds_of_detail(self):
        # Stated in the skill because the question arises mid-work, where a
        # reference one seam away would not be in context.
        assert has_paragraph_with(
            _body(), "operator", "code", "file path", "stack trace", "diagnostic code"
        )


def test_the_glossary_defines_the_term_this_skill_is_named_for():
    # A skill whose central noun is undefined is one two readers draw
    # differently; the queue's four statuses depend on the term.
    body = CONTEXT.read_text(encoding="utf-8")
    assert "**Conversion**:" in body, "convert is named for a term the glossary never defines"


class TestParking:
    """A Conversion needing the Operator is parked; the Migration is not stalled.

    Under Phases one unanswered question could hold up a whole Migration. For a
    customer onboarding onto Testsigma that is weeks of silence traceable to a
    single question nobody chased, and it is the failure parking exists to
    prevent.
    """

    def _parking(self):
        return DOC.section("Park")

    def _report(self):
        return DOC.section("Report")

    def test_no_hedge_grants_permission_to_stop_instead(self):
        # A permissive sentence added beside the rule is how "park rather than
        # stop" becomes "park where convenient".
        assert not hedges_in(self._parking()), "parking must not be optional"

    def test_it_parks_rather_than_stopping_the_migration(self):
        assert has_paragraph_with(
            self._parking(),
            "park",
            "only the operator",
            absent=("stop the migration", "wait for the answer"),
        ), "a Conversion that stops on an unanswered question stalls the Migration"

    def test_parking_sets_the_status_and_records_what_it_waits_on(self):
        assert has_paragraph_with(
            self._parking(), "`parked`", "`reason`", "waits on"
        )

    def test_the_reason_is_in_the_operators_terms_and_is_bound_by_the_rule(self):
        # `scenarios.md` is read back to the Operator by `resume`, so a Reason
        # holding a file path is a file path put in front of them. The four
        # forbidden kinds are not relisted here: `asking.md` decides them and
        # says a skill restating them need not.
        assert has_paragraph_with(
            self._parking(), "`reason`", "operator", "terms"
        ), "a Reason outside the rule is diagnostic detail shown to the Operator"

    def test_the_question_itself_goes_to_the_open_questions(self):
        # `Reason` says what is outstanding; `open-questions.md` is where the
        # Operator answers it. Without the second, parking records a wait with
        # nowhere to end it.
        assert has_paragraph_with(self._parking(), "`open-questions.md`", "answer")

    def test_having_parked_the_invocation_ends(self):
        # Parking is not a way around one-and-stop: the next Conversion is the
        # next invocation's, not this window's.
        assert has_paragraph_with(
            self._parking(),
            "ends",
            "another conversion",
            absent=("take the next scenario now", "continue with the next"),
        )

    def test_a_parked_conversion_is_taken_up_again_once_the_thing_clears(self):
        assert has_paragraph_with(
            self._parking(), "`pending`", "cleared"
        ), "a parked scenario nothing returns to pending is a scenario forgotten"

    def test_a_re_taken_conversion_goes_through_the_same_loop(self):
        assert has_paragraph_with(
            self._parking(),
            "same loop",
            absent=("resume where it left off", "second path"),
        )

    def test_residue_never_parks_a_conversion(self):
        assert has_paragraph_with(
            self._parking(),
            "residue",
            "never parks",
            "marker",
            absent=("parks the conversion",),
        ), "losing a whole test to a correctly declined step would be a regression"

    def test_the_operator_is_told_what_parked_and_why(self):
        # Told what parked and what it waits on — not a status the Operator
        # then has to go and decode somewhere else.
        report = self._report().lower()
        assert "parked" in report and "waits on" in report, (
            "a status the Operator must go and decode is not a report"
        )
