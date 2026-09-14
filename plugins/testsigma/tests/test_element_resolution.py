"""The shared element-resolution procedure, and its two callers.

`references/element-resolution.md` owns the decision procedure: the three places
an element comes from, their order, stopping at the first that answers, and what
happens when none does. Its callers own the *conduct* — collecting the list,
grouping by screen, how a human is asked, what is reported.

These assertions used to live in `test_map_skill.py`, under the name of one of
the callers, which is why the reference's own guarantees were hard to find and
why both skills could restate them unnoticed. The agreement test at the bottom
is the control that stops the restatement growing back.
"""

import re

import pytest

from support import (
    ADAPTERS_DIR,
    document,
    document_files,
    doc_id,
    PLUGIN_ROOT,
    REFERENCES_DIR,
    has_paragraph_with,
    read_frontmatter,
)

ELEMENT_RESOLUTION = REFERENCES_DIR / "element-resolution.md"
RESOLVE_ELEMENTS = PLUGIN_ROOT / "skills" / "resolve-elements" / "SKILL.md"
MAP = PLUGIN_ROOT / "skills" / "map" / "SKILL.md"
ASSEMBLE = PLUGIN_ROOT / "skills" / "assemble" / "SKILL.md"


DOC = document(ELEMENT_RESOLUTION)


def _text(needle=None):
    return DOC.body if needle is None else DOC.section(needle)


def _bold_leads(text):
    """The bold lead-ins of a section, in document order.

    The three places an element is looked for are bold-led items, so their
    order is structural rather than a matter of phrasing.
    """
    return re.findall(r"\*\*(.+?)\*\*", text)


# --- the procedure the reference owns ----------------------------------------

class TestTheProcedure:
    def test_the_three_places_are_tried_in_order(self):
        # Structural. "source" and "first" co-occur in the capture paragraph too
        # ("their time is the last resort and not the first"), which passed this
        # with the source demoted to "one option among three".
        #
        # The project leads, ahead of the source. This inverts the original
        # order deliberately. Where the source carries locators it answers every
        # time, so a project consulted second is a project never consulted — and
        # the duplicate screens that produces are what this procedure exists to
        # prevent. The source is still what supplies the locator; looking at the
        # project first is how a collision is noticed at all.
        leads = _bold_leads(_text())
        found = {}
        for index, lead in enumerate(leads):
            for place in ("source", "existing", "capture"):
                if place in lead.lower() and place not in found:
                    found[place] = index
        assert set(found) == {"source", "existing", "capture"}, (
            f"the three places an element comes from are not all named: {leads}"
        )
        assert found["existing"] < found["source"] < found["capture"], (
            f"the three places are out of order: {leads}"
        )
        assert "first" in leads[found["existing"]].lower(), (
            "the project must be named as the first place tried, not merely as one of them"
        )

    def test_it_stops_at_the_first_place_that_answers(self):
        assert has_paragraph_with(_text(), "stop at the first")

    def test_existing_screens_are_reused_by_name_before_anything_is_created(self):
        assert has_paragraph_with(
            _text(), "by name", "before", absent=("after creating",)
        ), "a Migration must not duplicate screens the Operator already maintains"

    def test_operator_capture_happens_only_when_nothing_else_can_supply_it(self):
        # "last resort" appears twice here, so the old assertion passed with the
        # condition on asking deleted.
        assert has_paragraph_with(_text(), "capture", "only when", "neither"), (
            "the Operator's time must be the last resort, not the first"
        )

    def test_an_unresolved_element_becomes_residue_with_that_cause(self):
        assert has_paragraph_with(
            _text(), "residue.md", "unresolved element", "distinct"
        ), "an unresolved element and an unexpressible step are distinct causes"

    def test_it_records_the_standing_of_what_it_writes_off(self):
        # An element nobody has captured yet is a gap; one the application
        # cannot expose is a refusal. This lived in two skills and not in the
        # document that owns what happens when nothing answers.
        assert has_paragraph_with(_text(), "standing", "gap", "refusal"), (
            "the reference decides what an unresolved element becomes, so the "
            "standing of that cause belongs here rather than in each caller"
        )

    def test_an_unresolved_element_blocks_assembly_rather_than_placeholding(self):
        assert has_paragraph_with(
            _text(), "block", "placeholder", absent=("assemble it anyway",)
        )

    def test_the_block_is_recorded_at_the_elements_granularity(self):
        assert has_paragraph_with(_text(), "granularity", "parameter value"), (
            "an unresolved element must not block the occurrences that resolved"
        )

    def test_element_count_is_not_estimated_from_the_step_count(self):
        assert has_paragraph_with(_text(), "distinct", "parameter values"), (
            "estimating element work as a proportion of Source Steps is badly wrong"
        )

    def test_it_disambiguates_a_colliding_name(self):
        assert has_paragraph_with(
            _text("naming"), "owning source class", "number"
        )


# --- what each caller owns ---------------------------------------------------

class TestTheCallers:
    def test_both_callers_point_at_it(self):
        for path in (MAP, RESOLVE_ELEMENTS):
            assert "references/element-resolution.md" in path.read_text(
                encoding="utf-8"
            ), f"{path.parent.name} runs the procedure without pointing at it"

    def test_resolve_elements_owns_the_gate_on_what_the_source_carries(self):
        # Whether this runs at all is a property of the source: where the
        # adapter carries locators, mapping has already answered in the same
        # reading, and running this would read those files twice.
        assert has_paragraph_with(
            RESOLVE_ELEMENTS.read_text(encoding="utf-8"),
            "carries-locators",
            "conversion",
        )

    def test_resolve_elements_is_something_convert_calls(self):
        # Its description used to declare it the way into a Phase, which got it
        # invoked as a bulk stage over a whole suite.
        meta, _ = read_frontmatter(RESOLVE_ELEMENTS)
        description = str(meta.get("description", "")).lower()
        assert "convert" in description and "screen" in description, (
            "the description must read as something a Conversion calls, scoped "
            "to one screen"
        )
        assert "phase" not in description

    def test_resolve_elements_is_scoped_to_the_screens_one_conversion_needs(self):
        body = RESOLVE_ELEMENTS.read_text(encoding="utf-8")
        assert has_paragraph_with(
            body,
            "this conversion",
            "screen",
            absent=("every element the step map names", "the whole suite"),
        ), "resolving elements no reviewed row of this scenario references is work spent on a guess"

    def test_the_operator_is_asked_for_a_whole_screen_at_once(self):
        # Capture is cheap per screen and expensive per visit: someone already
        # looking at a screen captures eight controls nearly as fast as one.
        assert has_paragraph_with(
            RESOLVE_ELEMENTS.read_text(encoding="utf-8"),
            "whole",
            "screen",
            absent=("one element at a time",),
        )

    def test_resolve_elements_owns_the_conduct_the_reference_does_not(self):
        body = RESOLVE_ELEMENTS.read_text(encoding="utf-8")
        # Grouping by screen, confirming a near match, and recording a capture
        # as it lands are the Phase's own — none is in the reference.
        assert has_paragraph_with(body, "group", "screen")
        assert has_paragraph_with(body, "nearly matches", "confirm")
        assert has_paragraph_with(body, "platform-facts.md", "twice")

    def test_resolve_elements_reports_residue_as_a_number_not_a_rule(self):
        # After the split it contributes a count to the report; the rule is the
        # reference's.
        assert has_paragraph_with(
            RESOLVE_ELEMENTS.read_text(encoding="utf-8"), "report", "residue"
        )


# --- the control ------------------------------------------------------------

#: The rules `element-resolution.md` owns, as the phrase that identifies each.
#: A caller carrying one of these is restating the procedure rather than running
#: it — which is what happened, in three documents, while 753 tests passed.
OWNED_BY_THE_REFERENCE = (
    "two of everything",
    "last resort and not the first",
    "never substitute a placeholder",
    "granularity",
    "distinct parameter values",
)

CALLERS = (RESOLVE_ELEMENTS, MAP, ASSEMBLE)


def _flat(text):
    """Whitespace-normalised and lowered.

    A markdown line wrap is not semantic, and three of the phrases below are
    wrapped in at least one document — matching the raw text would have made
    this control silently vacuous rather than failing loudly.
    """
    return " ".join(text.split()).lower()


@pytest.mark.parametrize("phrase", OWNED_BY_THE_REFERENCE)
def test_the_reference_states_each_rule_it_owns(phrase):
    assert phrase in _flat(_text()), (
        f"the reference is supposed to own {phrase!r} and does not state it"
    )


@pytest.mark.parametrize("path", CALLERS, ids=lambda p: p.parent.name)
@pytest.mark.parametrize("phrase", OWNED_BY_THE_REFERENCE)
def test_no_caller_restates_a_rule_the_reference_owns(path, phrase):
    # The failure this closes: every caller pointed at the reference AND
    # restated it, and no string test could tell the difference, because
    # "point at it" and "point at it then repeat it" are both a substring
    # match on the path.
    body = _flat(path.read_text(encoding="utf-8"))
    assert phrase not in body, (
        f"{path.parent.name} restates {phrase!r}, which "
        f"references/element-resolution.md owns; point at it instead"
    )



# --- element resolution is not a Phase --------------------------------------

#: Survey is the only Phase (ADR-0012). Element resolution happens inside a
#: Conversion, and a document still calling it a Phase is a document that gets
#: it invoked as a bulk stage over a whole suite — which is the order this
#: change exists to undo.
def test_no_document_calls_element_resolution_a_phase():
    from support import phase_claims, swept_documents

    offenders = {}
    for path in swept_documents():
        claims = phase_claims(path.read_text(encoding="utf-8"), subject="element")
        if claims:
            offenders[doc_id(path)] = claims
    assert not offenders, (
        f"these still frame element resolution as a Phase: {offenders}. Survey "
        "is the only Phase; resolution happens inside a Conversion."
    )


# --- the glossary does not order the first two places (ADR-0013) -------------

def test_the_adr_that_separates_looking_first_from_winning_is_tracked():
    from support import adr_files

    matching = [p for p in adr_files() if p.name.startswith("0013")]
    assert len(matching) == 1, (
        f"no ADR-0013 among {[p.name for p in adr_files()]}; the ordering was "
        "reversed once already and the reason must outlive this session"
    )
    body = matching[0].read_text(encoding="utf-8").lower()
    assert "target project, then the source" in body
    assert "last resort" in body


class TestTheGlossaryDefersTheOrdering:
    """One term was carrying two rules, and they pointed opposite ways.

    Where you *look* first is the project, so a name collision is noticed at
    all; which answer is *written* is the source, because that is what the test
    actually drove. The glossary stated a single order and was wrong as either.
    """

    def _entry(self):
        body = document(PLUGIN_ROOT / "CONTEXT.md").body
        start = body.index("**Element Resolution**:")
        return " ".join(body[start:body.index("\n\n", start)].split()).lower()

    def test_it_names_all_three_places(self):
        entry = self._entry()
        for place in ("target project", "source", "operator capture"):
            assert place in entry, f"the glossary does not name {place}"

    def test_it_states_only_that_operator_capture_is_last(self):
        entry = self._entry()
        assert "last resort" in entry
        assert "in that order" not in entry, (
            "ordering the first two places here contradicts the procedure; "
            "references/element-resolution.md owns it"
        )

    def test_it_points_at_the_decision_rather_than_repeating_it(self):
        assert "adr-0013" in self._entry()
