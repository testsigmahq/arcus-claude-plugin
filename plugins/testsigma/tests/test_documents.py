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
