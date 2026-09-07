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
    PLUGIN_ROOT,
    REFERENCES_DIR,
    has_paragraph_with,
    markdown_sections,
)

ELEMENT_RESOLUTION = REFERENCES_DIR / "element-resolution.md"
RESOLVE_ELEMENTS = PLUGIN_ROOT / "skills" / "resolve-elements" / "SKILL.md"
MAP = PLUGIN_ROOT / "skills" / "map" / "SKILL.md"
ASSEMBLE = PLUGIN_ROOT / "skills" / "assemble" / "SKILL.md"


def _text(needle=None):
    text = ELEMENT_RESOLUTION.read_text(encoding="utf-8")
    if needle is None:
        return text
    sections = markdown_sections(text)
    matching = [v for k, v in sections.items() if needle in k.lower()]
    assert len(matching) == 1, f"expected one section for {needle!r}: {list(sections)}"
    return matching[0]


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
        leads = _bold_leads(_text())
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

    def test_resolve_elements_owns_the_gate_that_makes_it_a_phase(self):
        # Whether this is a Phase of its own is a property of the source.
        assert has_paragraph_with(
            RESOLVE_ELEMENTS.read_text(encoding="utf-8"), "carries-locators", "phase"
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

