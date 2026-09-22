"""The fault-class catalogue's index, and the division it indexes.

`map` orders this document worked through *for each Step Map row*, and until
this module the document promised "It is short on purpose" while running to
5,484 words across 28 sections with no entry point. Two separate defects sat
behind that sentence: no index, and two kinds of content filed as one — things
to look for in a row, and rules about how the comparison is conducted.

The index orders the reading; it never narrows it. Every entry is a fault that
already reached a converted test that compiled, was accepted by the tenant and
survived a round trip, so an index that licensed reading four entries of twenty
would be recall with better formatting — which is the thing `map` says not to
trust. These tests hold that line, and hold the index in step with the
headings, which is the drift nothing could see: Candidate 2 added a section and
no test noticed there was nothing to add it to.
"""

import re

from support import (
    REFERENCES_DIR,
    SKILLS_DIR,
    command_files,
    document,
    has_paragraph_with,
    skill_files,
)

CATALOGUE = document(REFERENCES_DIR / "fault-classes.md")
AUTHORING = document(REFERENCES_DIR / "authoring.md")
MAP = document(SKILLS_DIR / "map" / "SKILL.md")

#: The two parts, by a word their headings carry. The first is read per row;
#: the second once at the start of a Migration.
PER_ROW_PART = "fault classes"
CONDUCT_PART = "conducting"

#: The index's own heading. It is a `##` inside the per-row part, so it has to
#: be excluded from the set of entries it covers.
INDEX_HEADING = "Where to start for the row in hand"


def _headings(text):
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def _index_body():
    part = CATALOGUE.part(PER_ROW_PART)
    sections = {h: b for h, b in zip(_headings(part), _split_sections(part))}
    assert INDEX_HEADING in sections, (
        f"the per-row part carries no `## {INDEX_HEADING}`; its headings are "
        f"{list(sections)}"
    )
    return sections[INDEX_HEADING]


def _split_sections(part):
    """Bodies of the `##` sections of one part, in order."""
    bodies, buffer, started = [], [], False
    for line in part.splitlines():
        if line.startswith("## "):
            if started:
                bodies.append("\n".join(buffer))
            started, buffer = True, []
        elif started:
            buffer.append(line)
    if started:
        bodies.append("\n".join(buffer))
    return bodies


def _routed_entries():
    """Every entry the index's routing table names, from its second column.

    Scoped to the table's second column rather than to every backticked run in
    the section. The first cut filtered candidates by `q[0].isupper() and " "
    in q`, which let a phantom single-word or lowercase entry through — a hole
    in the very control written to catch a hole.
    """
    entries = set()
    for line in _index_body().splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 2 or not cells[1].startswith("`"):
            continue
        entries.update(re.findall(r"`([^`]+)`", cells[1]))
    return entries


def _fault_classes():
    return [h for h in _headings(CATALOGUE.part(PER_ROW_PART)) if h != INDEX_HEADING]


def _conduct_rules():
    return _headings(CATALOGUE.part(CONDUCT_PART))


def test_the_document_is_divided_into_the_two_kinds_of_content():
    # Read per row against read once per Migration. Filed together, the per-row
    # instruction pointed at session-level material, which is how the "short on
    # purpose" claim survived: nobody working a row reached the far half.
    parts = CATALOGUE.parts
    assert len(parts) == 2, f"expected two `# ` parts, found {list(parts)}"
    CATALOGUE.part(PER_ROW_PART)
    CATALOGUE.part(CONDUCT_PART)


def test_the_index_and_the_entries_are_the_same_set():
    # Both directions, as one equality. Forward: an entry the index cannot
    # reach is never read first for the row it belongs to. Backward: an index
    # naming a heading that was reworded routes a reader at nothing, and reads
    # as though it routed them somewhere.
    assert _routed_entries() == set(_fault_classes()), (
        f"index names {sorted(_routed_entries() - set(_fault_classes()))} which "
        f"are not entries, and omits "
        f"{sorted(set(_fault_classes()) - _routed_entries())}"
    )


def test_no_conduct_rule_is_named_in_the_index():
    # The index routes a row. A session-level rule reached from it would be
    # read per row and skipped when the row's text did not mention it, which is
    # the wrong frequency in both directions.
    leaked = [h for h in _conduct_rules() if h in _routed_entries()]
    assert not leaked, (
        f"these are rules about conducting the comparison, not entries to "
        f"route a row to: {leaked}"
    )


def test_the_index_orders_the_reading_without_narrowing_it():
    # The load-bearing one. Every entry here already survived compile, tenant
    # acceptance and a round trip, so no row is exempt from any of them.
    index = " ".join(_index_body().split()).lower()
    assert "does not narrow" in index, (
        "the index must say outright that it orders the reading rather than "
        "selecting from it, adjacent to the routing itself"
    )
    assert "every entry" in index, (
        "and must say that every entry still applies to every row"
    )
    assert "no trigger is a precondition" in index, (
        "and must say that a row matching no trigger still gets the whole part"
    )


def test_the_opening_no_longer_claims_the_list_is_short():
    # It said "It is short on purpose" at 5,484 words. A false promise inside a
    # module's own interface discredits the instruction it was supporting.
    # Normalised, because the claim was wrapped as "It is short on\npurpose."
    # and a raw substring check would have passed against it — the vacuous
    # control this suite has produced twice before.
    assert "short on purpose" not in CATALOGUE.flat, (
        "the catalogue is not short; the index is what makes it workable"
    )


def test_the_per_row_instruction_stays_with_the_catalogue():
    # Stripping the false claim must not take the instruction with it.
    opening = " ".join(CATALOGUE.part(PER_ROW_PART).split()).lower()
    assert "each step map row" in opening or "every step map row" in opening, (
        "the preamble must still say this is worked per Step Map row"
    )


def test_the_conduct_part_is_scheduled_by_the_stage_that_uses_it():
    # The consequence of the split. Those rules used to be swept into `map`'s
    # per-row instruction — read at the wrong frequency, but read. Taking them
    # out of that loop leaves nothing scheduling them at all unless the stage
    # names them once, which is the whole point of dividing the document by
    # reading frequency rather than by subject.
    step_zero = " ".join(MAP.section("step 0").split()).lower()
    assert "conducting the comparison" in step_zero, (
        "map's once-per-stage step must name the part of fault-classes.md that "
        "is read once per stage"
    )
    assert "once" in step_zero, "and must say it is read once rather than per row"


def test_a_helper_is_compared_by_its_state_semantics_not_only_its_name():
    section = CATALOGUE.section("helper's state semantics")
    assert has_paragraph_with(section, "trim", "replace", "wait"), (
        "a Java helper can preserve its name while losing normalization, mutation, or timing"
    )


def test_textarea_reads_preserve_value_attribute_semantics():
    section = CATALOGUE.section("helper's state semantics")
    assert has_paragraph_with(
        section, "textarea", "getAttribute", "value", "visible text"
    ), "textarea state must not be mapped to an element-text read"


def test_no_document_points_at_the_catalogue_without_a_section():
    # Two bare-filename pointers into a 28-section document. A pointer that
    # names the file only asks the reader to search it, and at this size that
    # is the same as not pointing.
    bare = []
    for path in _documents():
        text = path.read_text(encoding="utf-8")
        bare += [
            f"{path.name}: {match.group(0)}"
            for match in re.finditer(r"`[^`]*fault-classes\.md(#[\w-]*)?`", text)
            if not match.group(1)
        ]
    assert not bare, f"fault-classes.md named with no section anchor: {bare}"


def test_every_anchor_into_the_catalogue_resolves_to_a_heading():
    # An anchor is only worth more than a filename if it lands. Slugs are
    # GitHub-style: lowercased, non-word characters dropped, spaces hyphenated.
    def slug(heading):
        return re.sub(r"[^\w\s-]", "", heading.lower()).strip().replace(" ", "-")

    slugs = {slug(h) for h in _headings(CATALOGUE.text)}
    slugs |= {slug(h) for h in CATALOGUE.parts}
    for path in _documents():
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"fault-classes\.md#([\w-]+)", text):
            assert match.group(1) in slugs, (
                f"{path.name} anchors at #{match.group(1)}, which is not a "
                f"heading in fault-classes.md"
            )


def _documents():
    """Every document that could point at the catalogue."""
    return sorted(REFERENCES_DIR.glob("*.md")) + list(skill_files()) + list(command_files())
