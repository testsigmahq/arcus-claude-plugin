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
    REFERENCES_DIR,
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

    def test_the_comparison_starts_with_call_chain_coverage(self):
        # Six of twenty-one measured defects were a composite converted
        # partway, so coverage of the call chain is the primary check and the
        # skill must lead with it rather than only cite the catalogue.
        section = _section("compare")
        assert has_paragraph_with(
            section, "coverage of the call chain", "transitively"
        ), "the largest class of defect is found by walking the calls"
        assert has_paragraph_with(
            section, "map to none"
        ), "the unmapped calls are the finding"

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


# --- learnings from the INT-26 conversion verification ------------------------
#
# A step-by-step static comparison of the first conversion, eleven source steps
# deep, produced fault classes this plugin did not name. Each assertion below
# traces to a finding in that analysis rather than to a guess about what might
# go wrong. The catalogue lives in a reference because the skill body is bounded.

FAULT_CLASSES = REFERENCES_DIR / "fault-classes.md"


def _fault_section(needle):
    sections = markdown_sections(FAULT_CLASSES.read_text(encoding="utf-8"))
    matching = [v for k, v in sections.items() if needle in k.lower()]
    assert len(matching) == 1, (
        f"expected one section containing {needle!r}, found {len(matching)}: "
        f"{list(sections)}"
    )
    return matching[0]


class TestTheFaultClassCatalogue:
    def test_it_exists_and_the_comparison_step_points_at_it(self):
        assert FAULT_CLASSES.is_file()
        # Scoped to the step that must use it. Asserted against the whole body,
        # a stray mention anywhere would satisfy this while the comparison
        # never worked through the catalogue.
        assert "references/fault-classes.md" in _section("compare"), (
            "the catalogue is worked through while comparing, so the comparison "
            "step must point at it"
        )
        assert has_paragraph_with(_section("compare"), "work through", "every row")

    def test_a_lost_non_default_argument_is_its_own_fault(self):
        # Finding 2b: the source waited 60 seconds, the converted step declared
        # no timeout and silently took the platform default of 30. The step is
        # present and looks right; only the argument was lost.
        section = _fault_section("non-default argument")
        assert has_paragraph_with(section, "arguments", "not only the actions")

    def test_one_verb_serving_two_source_constructs_is_counted_separately(self):
        # The wait ledger: explicit source steps and implicit helper calls both
        # became the same verb, so a count of eighteen said nothing about
        # whether any particular one was dropped.
        section = _fault_section("two source constructs")
        assert has_paragraph_with(section, "separately", "ledgers")
        assert has_paragraph_with(section, "dropped step", "fidelity"), (
            "the two ledgers differ in severity as well as in origin"
        )

    def test_an_improvement_on_the_source_is_a_divergence_too(self):
        # Finding 9b: the source's uniqueness was weaker than the conversion's.
        section = _fault_section("improves on the source")
        assert has_paragraph_with(section, "question", "fidelity")

    def test_a_fault_is_reported_with_where_it_surfaces(self):
        # Findings 3a and 7a: a wrong business unit passed every step and
        # surfaced minutes later as an unrelated poll timing out.
        section = _fault_section("surfaces far from its cause")
        assert has_paragraph_with(section, "where it will surface", "where it is")

    def test_partial_absence_is_read_as_omission(self):
        # Finding 4a: the conversion cleared the field at four sites and not at
        # four others. Uniform absence is a decision; partial absence is a bug.
        section = _fault_section("partial absence")
        assert has_paragraph_with(section, "every site", "not only")

    def test_an_unrunnable_conversion_changes_the_standard_of_evidence(self):
        # The constraint the analysis opens with: the test cannot be executed,
        # so static comparison is the only gate.
        section = _fault_section("cannot be run")
        assert has_paragraph_with(section, "absence of evidence is not")
        assert has_paragraph_with(
            section, "fidelity", "unverifiable"
        ), "prefer fidelity when the result cannot be observed"

    def test_verb_semantics_are_platform_facts_established_before_use(self):
        # A text-entry verb was assumed to clear the field. It appends. The
        # assumption had already been recorded as a fact and had to be corrected.
        section = _fault_section("verb semantics")
        assert has_paragraph_with(section, "platform-facts.md", "probing")
        assert has_paragraph_with(
            section, "weaker and more brittle"
        ), "equivalence is not a single axis"

    def test_a_readiness_check_answering_the_wrong_question_has_its_own_entry(self):
        # The analysis' largest single finding: document readiness goes true
        # when the shell loads and says nothing about whether the view settled.
        section = _fault_section("readiness check")
        assert has_paragraph_with(section, "did the shell load", "did this view settle")
        assert has_paragraph_with(
            section, "second thing to add", "detail"
        ), "an app-specific settling wait is a separate wait, not a refinement"

    def test_a_verb_addressing_a_different_thing_has_its_own_entry(self):
        # Distinct from what a verb does: what it does it to. The source pressed
        # Enter against a named element; the platform's verb hits whatever has
        # focus, and no element-scoped equivalent exists.
        section = _fault_section("addresses a different thing")
        assert has_paragraph_with(section, "focus", "element-scoped")
        assert has_paragraph_with(
            section, "three things and not one", "on failure"
        ), "what it does, what it does it to, and what it does on failure"

    def test_a_race_that_commits_a_wrong_value_is_not_filed_as_flakiness(self):
        # Around an asynchronously populated field a missing wait passes while
        # committing a value nobody chose.
        section = _fault_section("commits the wrong value")
        assert has_paragraph_with(
            section, "correctness finding", "stability"
        ), "a missing wait here is a correctness fault, not a flaky one"

    def test_a_verb_can_be_weaker_and_more_brittle_at_once(self):
        section = _fault_section("verb semantics")
        assert has_paragraph_with(section, "weaker and more brittle", "both directions")

    def test_name_convergence_raises_the_priority_of_opening_the_helper(self):
        # From the session behind the analysis: the closer two constructs'
        # names are, the less likely anyone checks them, which is why the
        # readiness fault took eleven steps to surface.
        section = _fault_section("names that match")
        assert has_paragraph_with(
            section, "name convergence", "raises the priority"
        ), "the instinct must be inverted, not merely noted"
        assert has_paragraph_with(section, "less likely anyone checks")

    def test_a_name_that_drifted_from_its_behaviour_has_an_entry(self):
        # A step named for waiting had both wait calls commented out and
        # replaced by unconditional sleeps.
        section = _fault_section("drifted from its behaviour")
        assert has_paragraph_with(section, "commented-out code is behaviour")
        assert has_paragraph_with(
            section, "names are historical", "normal state"
        ), "drift is the normal state in a mature suite, not the exception"

    def test_a_sleep_is_treated_as_semantics_rather_than_a_smell(self):
        section = _fault_section("drifted from its behaviour")
        assert has_paragraph_with(
            section, "refactor", "translation"
        ), "reproduce the timing and let the owning team refactor later"

    def test_every_finding_records_its_direction(self):
        # The conversion was lossy on timing and stronger on interaction. A
        # count of findings cannot tell a halved timeout from a better click.
        section = _fault_section("direction of every finding")
        assert has_paragraph_with(section, "lossy", "stronger")
        assert has_paragraph_with(
            section, "loss", "gain"
        ), "a loss is a fidelity finding; a gain is a question"

    def test_a_count_mismatch_is_a_question_before_it_is_a_defect(self):
        # Five clicks against four steps: the extra one was correct, hidden in
        # a Composite Step. Assuming the count was wrong would have deleted it.
        section = _fault_section("count that does not match")
        assert has_paragraph_with(section, "question", "until you have found")

    def test_the_platforms_own_strings_are_a_source_of_platform_facts(self):
        # The readiness gap was discoverable from the target side alone: the
        # verb's success message warns that SPAs need an element wait.
        section = _fault_section("verb semantics")
        assert has_paragraph_with(
            section, "success message warns"
        ), "a verb's own messages are Platform Facts waiting to be read"

    def test_a_format_string_is_treated_as_a_program(self):
        # The sharpest fault in the pass: the same pattern letter means
        # fraction-of-second in one date API and millisecond in another, so
        # copying the pattern text produced a value 11 characters longer.
        section = _fault_section("format string")
        assert has_paragraph_with(section, "re-derived from the rendered")
        assert has_paragraph_with(
            section, "render a sample", "diff the length"
        ), "the mechanical check is what caught it"
        assert has_paragraph_with(
            section, "round trip cannot see this"
        ), "no automated check reaches this class"

    def test_a_value_transformed_on_its_way_to_the_browser_has_an_entry(self):
        # One test-data key needed two different strings, because a step
        # definition three calls deep applied a replace on the way to typing.
        section = _fault_section("way to the browser")
        assert has_paragraph_with(section, "what", "actually reaches the browser")
        assert has_paragraph_with(
            section, "expression", "rather than the source literal"
        ), "record what is typed, not what is written"

    def test_every_numeric_argument_is_a_candidate_lost_default(self):
        section = _fault_section("non-default argument")
        assert has_paragraph_with(section, "numeric argument", "candidate")
        assert has_paragraph_with(
            section, "waits and retries"
        ), "that is where a lost value is least visible and matters most"
        assert has_paragraph_with(
            section, "legal value is not a faithful one"
        )

    def test_the_authority_chain_runs_to_the_implementation(self):
        section = _fault_section("verb semantics")
        assert has_paragraph_with(
            section, "more than one hop", "snippet class"
        ), "the catalogue settles nothing about behaviour"
        assert has_paragraph_with(
            section, "turn it into a sweep"
        ), "a settled semantic becomes a mechanical rule for the whole suite"

    def test_a_verdict_without_the_implementation_is_provisional(self):
        # Every early verdict in the pass was given before the jar was opened.
        section = _fault_section("without the implementation")
        assert has_paragraph_with(
            section, "before starting", "partway through"
        ), "obtain the implementation first"
        assert has_paragraph_with(
            section, "re-open", "provisional"
        ), "a verdict reached from intent was not a check"

    def test_a_dropped_side_effect_is_judged_by_its_consumers(self):
        # One captured handle nothing read: benign, proven by grepping all 42
        # source lines. One captured document a later step read: a defect.
        section = _fault_section("side effect")
        assert has_paragraph_with(section, "consumers", "before judging it")

    def test_a_concession_may_originate_in_an_earlier_row(self):
        # The killer case: a later step's weaker assertion was faithful to its
        # own line, and the fault was the capture missing several steps back.
        section = _fault_section("side effect")
        assert has_paragraph_with(
            section, "originate", "earlier"
        ), "recording a Concession where it appears legitimises the omission"

    def test_a_heuristic_script_over_source_is_refused(self):
        # Three false results in one pass, including a comment stripper that
        # deleted every XPath because an XPath begins with two slashes.
        section = _fault_section("heuristic script")
        assert has_paragraph_with(section, "exact by construction")
        assert has_paragraph_with(
            section, "one false positive and no true positives"
        ), "the arithmetic is the argument"
        assert has_paragraph_with(
            section, "targeted check", "broad sweep"
        )

    def test_a_positional_heuristic_drops_and_invents_at_once(self):
        # Every wait before an action dropped, every wait after kept, and three
        # invented with no source counterpart. The totals looked plausible.
        section = _fault_section("positional heuristic")
        assert has_paragraph_with(section, "by position", "rather than")
        assert has_paragraph_with(
            section, "cancel in a total"
        ), "a dropped step and an invented one hide each other"

    def test_a_smarter_target_can_create_a_new_failure_mode(self):
        section = _fault_section("smarter")
        assert has_paragraph_with(
            section, "not the end of the comparison"
        ), "an improvement meeting the source's weaknesses is a new risk"

    def test_a_findings_count_and_cause_both_drift(self):
        # Four sites became six; an element total was wrong by four for a dozen
        # steps; an "invented locator" was really one lifted from the wrong class.
        section = _fault_section("count and its cause")
        assert has_paragraph_with(section, "re-count", "new sites")
        assert has_paragraph_with(
            section, "verdict can be right while the cause is wrong"
        ), "and the cause is the half the fix is built on"

    def test_a_composite_converted_partway_is_the_largest_class(self):
        # Six of twenty-one defects. One source line resolves to a method
        # making several calls; the conversion took the first and stopped.
        section = _fault_section("converted partway")
        assert has_paragraph_with(section, "transitively", "at least one target step")
        assert has_paragraph_with(
            section, "report the calls that map to none"
        ), "the check is coverage, and it is mechanical"
        assert has_paragraph_with(
            section, "no whole-suite sweep", "secondary"
        ), "three element audits found one defect and two false positives"

    def test_an_element_is_bound_from_the_call_site_not_the_corpus(self):
        # Four defects were a locator that genuinely exists in the source,
        # lifted from the wrong place in it.
        section = _fault_section("rather than from the call site")
        assert has_paragraph_with(
            section, "provenance check passes on all four"
        ), "does this locator exist in the source is the wrong question"
        assert has_paragraph_with(section, "call chain reaches")
        assert has_paragraph_with(
            section, "coin toss"
        ), "a byFoo1 beside byFoo means both are live"

    def test_a_timeout_above_the_limit_silently_disables_the_wait(self):
        # Mechanically checkable, not a matter of judgement: the helper
        # returns nothing outside 1..120.
        section = _fault_section("verb semantics")
        assert has_paragraph_with(section, "silently disables", "120")
        assert has_paragraph_with(
            section, "worse than", "default"
        ), "raising a timeout past the limit is worse than leaving it alone"

    def test_the_text_verb_reads_markup_rather_than_value(self):
        section = _fault_section("verb semantics")
        assert has_paragraph_with(
            section, "text area", "value"
        ), "on a text area the live content is the value, not the markup"

    def test_defensive_source_code_is_read_as_a_prediction(self):
        # Sleeps, retries, fallbacks and duplicate locators mark where somebody
        # hit a problem in the application and worked around it.
        section = _fault_section("rough edges")
        assert has_paragraph_with(section, "predict", "fragile")
        assert has_paragraph_with(
            section, "note its defences separately"
        ), "they are the previous team's findings about the application"
        assert has_paragraph_with(
            section, "title", "twenty-second wait"
        ), "the measured example is what makes this concrete"

    def test_every_entry_says_it_already_happened(self):
        # A catalogue of imagined faults would grow without limit. These are
        # bounded by what got through a real conversion.
        body = FAULT_CLASSES.read_text(encoding="utf-8")
        assert has_paragraph_with(body, "measured", "already")


class TestAConcessionIsRecordedRatherThanHidden:
    def test_the_glossary_defines_it_as_the_third_state(self):
        from support import CONTEXT

        entry = CONTEXT.read_text(encoding="utf-8")
        assert "**Concession**" in entry, "Residue and Divergence left a gap"
        # Whitespace-normalised: the phrase straddles a line wrap, and a
        # markdown wrap is not semantic. has_paragraph_with does this for us;
        # a plain `in` over a glossary entry does not.
        block = " ".join(
            entry.split("**Concession**")[1].split("_Avoid_")[0].split()
        ).lower()
        assert "residue" in block and "divergence" in block, (
            "the term only means anything against the two it sits between"
        )
        assert "unrecorded concession is a divergence" in block, (
            "an unrecorded Concession is a Divergence, and that is the only "
            "thing separating them"
        )

    def test_the_skill_has_a_step_for_it(self):
        sections = [h for h in markdown_sections(_body()) if "concession" in h.lower()]
        assert len(sections) == 1, (
            f"a mention anywhere is not a step; headings are {list(markdown_sections(_body()))}"
        )

    def test_it_is_anchored_to_a_measured_case_like_every_fault_class(self):
        # Review: every fault-class entry cites a real instance and this did
        # not. The condition-with-no-presence-verb case is the cleanest one.
        assert has_paragraph_with(
            _section("concession"), "measured case", "not visible"
        ), "the model needs the instance it was invented to name"

    def test_a_concession_is_written_with_a_marker_resume_can_find(self):
        # The whole claim is "known and written down". Nothing made it findable
        # until the marker existed: resume counted unreviewed rows and read the
        # question files, and never looked at a reviewed row's content.
        assert has_paragraph_with(
            _section("concession"), "concession:", "resume"
        ), "a Concession nobody can find again is a Divergence"

    def test_a_concession_carries_the_platform_limit_that_forced_it(self):
        assert has_paragraph_with(
            _section("concession"), "platform-facts.md", "no"
        ), "the limit that forced the concession is a Platform Fact"

    def test_a_concession_does_not_block_assembly(self):
        assert has_paragraph_with(
            _section("concession"), "does not block assembly", "residue"
        ), "a concession is expressed work; Residue is declined work"

    def test_an_unrecorded_concession_is_a_divergence(self):
        assert has_paragraph_with(_section("concession"), "divergence", "written down")
