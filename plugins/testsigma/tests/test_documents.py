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
    """Every prose document in the plugin: skills, commands, references, adapters."""
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
