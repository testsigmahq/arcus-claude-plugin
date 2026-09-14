"""Invariants that hold across every document in the plugin.

These exist because section-scoped assertions have a blind spot by
construction. `markdown_sections` discards everything above the first `##`, so a
rule can be revoked in a document's preamble without any section test seeing it
— demonstrated by a review, which put a carve-out for reusing a stale tenant
result in one preamble and left the suite green.
"""

import pytest

from support import (
    ADAPTERS_DIR,
    REFERENCES_DIR,
    command_files,
    hedges_in,
    preamble,
    skill_files,
)


def _every_document():
    """Every prose document in the plugin: skills, commands, references, adapters.

    The glossary and the README are not in it. Where a check wants those too —
    a retired term has to be gone from everything a reader meets — reach for
    `swept_documents()` in `support`, which is that set plus these.
    """
    documents = list(skill_files()) + list(command_files())
    for directory in (REFERENCES_DIR, ADAPTERS_DIR):
        if directory.is_dir():
            documents.extend(sorted(directory.glob("*.md")))
    return documents


def _identify(path):
    return path.parent.name if path.name == "SKILL.md" else path.stem


DOCUMENTS = _every_document()


def test_there_are_documents_to_check():
    assert len(DOCUMENTS) >= 8, f"only found {len(DOCUMENTS)} documents"


@pytest.mark.parametrize("document", DOCUMENTS, ids=_identify)
def test_no_documents_preamble_grants_an_exception(document):
    # The preamble is where a carve-out hides from every section-scoped test.
    found = hedges_in(preamble(document.read_text(encoding="utf-8")))
    assert not found, (
        f"{document.name}'s preamble grants an exception to the rules below "
        f"it: {found}"
    )


# A whole-document version of the check above was written and then removed. It
# failed the survey skill on "treat below 1.5 as the warning threshold, as a
# guideline rather than a rule", which is a deliberate design decision and
# exactly right: that threshold is a guideline. The scanner cannot tell an
# intended guideline from a walk-back, so applied everywhere it would pressure
# honest prose into contortions to please a test. Scoped to preambles it has a
# demonstrated bypass to close and no legitimate prose to fight.


class TestEnumerationIsProbedBeforeCompiling:
    """ADR-0006 said nothing could enumerate the catalogue. Two things now can.

    The rule "hold no catalogue" is only sound where a probe exists. Where none
    does it silently becomes "know it already", and an agent that knows neither
    guesses against the validator.
    """

    def _probe(self):
        from support import REFERENCES_DIR, document
        return " ".join(document(REFERENCES_DIR / "cli-probe.md").flat.split())

    def test_the_probe_reference_names_both_enumerations(self):
        body = self._probe()
        assert "list verbs" in body and "list blocks" in body, (
            "a reference that governs probing must name the probes, or every "
            "stage rediscovers them"
        )

    def test_it_says_enumerate_before_compiling(self):
        assert "enumerate first" in self._probe(), (
            "compiling to discover a spelling rather than to confirm one is "
            "the failure this section exists to stop"
        )

    def test_it_says_a_missing_api_category_is_the_wrong_question(self):
        # `list verbs --category api` is refused. Read as a capability answer,
        # that refusal says api steps cannot be expressed, which is false.
        assert "wrong question" in self._probe()

    def test_the_amendment_is_recorded_as_a_decision(self):
        from support import PLUGIN_ROOT
        adr = PLUGIN_ROOT / "docs" / "adr" / "0009-the-build-enumerates-now-so-ask-it-first.md"
        assert adr.is_file(), "overturning a stated premise of an ADR is a decision"
        text = adr.read_text(encoding="utf-8")
        assert "ADR-0006" in text, "an amendment must name what it amends"


# --- the Phase framing is retired (ADR-0012) ---------------------------------


def test_no_document_frames_its_stage_as_a_phase():
    """The contract half of ADR-0012, swept across everything a reader meets.

    Mapping, element resolution and assembly are the steps inside a Conversion
    and run once per Conversion. A document still calling its stage a Phase
    tells a reader the Migration proceeds in bulk stages — whole Step Map
    reviewed, then every test assembled — which is the order the Conversion loop
    replaced, and the order that delivers no test for three weeks.

    `CONTEXT.md` is swept too: it is the glossary, and its Phase entry is the
    authority that says survey is the only one, so it passes by denial rather
    than by exemption.
    """
    from support import doc_id, phase_claims, swept_documents

    offenders = {}
    for path in swept_documents():
        found = phase_claims(path.read_text(encoding="utf-8"))
        if found:
            offenders[doc_id(path)] = found
    assert not offenders, (
        f"these still frame a stage of a Migration as a Phase: {offenders}. "
        "Survey is the only Phase; mapping, element resolution and assembly "
        "happen inside one Conversion."
    )


def test_the_glossary_still_defines_the_one_phase_there_is():
    # The sweep above is an absence check, and an absence check passes when the
    # term is deleted everywhere. Survey *is* a Phase, and a reader meeting the
    # word in ADR-0012 needs the glossary to still say what it means.
    from support import PLUGIN_ROOT, document

    entry = document(PLUGIN_ROOT / "CONTEXT.md").body
    start = entry.index("**Phase**:")
    entry = " ".join(entry[start:entry.index("**Conversion**:", start)].split()).lower()
    assert "survey is the only one" in entry
    # And that the word a skill uses for itself is not the term under another
    # spelling, since every skill calls its own work a stage.
    assert "stage" in entry, (
        "the glossary must settle what a skill means by 'stage', or the term "
        "is retired in spelling and kept in substance"
    )


def test_assembly_does_not_wait_for_the_rest_of_the_step_map():
    """The assumption the Phase framing carried, which outlives the word.

    A document can drop "Phase" and still tell a reader to finish mapping
    before building anything. Asserted positively, on the rule that makes the
    difference: a scenario whose own rows are reviewed is assembled now, and
    one waiting on a row is left with the row named — per scenario, not per
    Step Map. A phrase blacklist cannot see this; it passes on every wording
    nobody happened to list.
    """
    from support import SKILLS_DIR, document, has_paragraph_with

    body = document(SKILLS_DIR / "assemble" / "SKILL.md").body
    assert has_paragraph_with(
        body,
        "scenario",
        "not yet reviewed",
        absent=("all rows", "whole step map", "once every row"),
    ), (
        "assembly must say what happens to the one scenario waiting on a row, "
        "or a reader takes an unreviewed row anywhere as a reason to wait"
    )
