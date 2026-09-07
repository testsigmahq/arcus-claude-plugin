"""ADR-0006: the plugin holds no catalogue, and interrogates one instead.

The decision is epistemic and the documents are its whole implementation, so
these tests hold the documents to it: that the mechanism named is one an
installed CLI can actually perform, that the diagnostics it leans on are named
per ADR-0003, and that the throwaway workspace the mechanism needs cannot be
pushed.
"""

import pytest

from support import (
    document,
    CONTEXT,
    REFERENCES_DIR,
    adr_files,
    has_paragraph_with,
    paragraphs,
    skill_files,
)

AUTHORING = REFERENCES_DIR / "authoring.md"
PROBE = REFERENCES_DIR / "cli-probe.md"
CHECKS = REFERENCES_DIR / "checks.md"
DIRECTORY = REFERENCES_DIR / "migration-directory.md"


def _adr():
    matching = [p for p in adr_files() if p.name.startswith("0006")]
    assert len(matching) == 1, f"no ADR-0006 among {[p.name for p in adr_files()]}"
    return matching[0].read_text(encoding="utf-8")


# --- the decision ------------------------------------------------------------

class TestTheAdr:
    def test_it_exists_and_says_the_plugin_holds_no_catalogue(self):
        body = _adr().lower()
        assert "catalogue" in body
        assert "no catalogue" in body or "holds none" in body

    def test_it_extends_rather_than_competes_with_the_probe_adr(self):
        # Two ADRs answering the same question differently is the failure this
        # one is most likely to cause.
        assert "0003" in _adr(), (
            "ADR-0006 governs the object where 0003 governs the epistemics; "
            "unlinked, a later reader gets two answers"
        )

    def test_it_records_the_alternatives_that_were_rejected(self):
        body = _adr().lower()
        # The hand-written reference is the one that keeps getting proposed.
        assert "reference" in body or "document" in body
        # And the scrape is the one that looks like it works.
        assert "bundle" in body or "minified" in body or "scrape" in body

    def test_it_says_the_catalogue_is_never_enumerated(self):
        assert has_paragraph_with(_adr(), "enumerat"), (
            "the distinction between interrogating and enumerating is the whole "
            "of what this build can and cannot do"
        )


# --- the mechanism is one an install can perform -----------------------------

DOCUMENTS = sorted(REFERENCES_DIR.glob("*.md")) + list(skill_files())


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: p.parent.name + "/" + p.name)
def test_no_document_sends_a_session_to_the_language_server(path):
    # It is `private: true`, is not in the CLI's published files, and its own
    # dist resolves its dependencies externally, so it runs only inside a built
    # checkout of the CLI's monorepo. Two documents named it as the way to read
    # the schema, which is an instruction that cannot be carried out.
    body = path.read_text(encoding="utf-8")
    for block in paragraphs(body):
        lowered = " ".join(block.split()).lower()
        if "language server" not in lowered:
            continue
        assert "not" in lowered and (
            "install" in lowered or "ship" in lowered or "publish" in lowered
        ), (
            f"{path.name} mentions the language server without saying it is "
            f"unavailable from an install: {lowered[:120]}"
        )


class TestTheOracle:
    def _section(self):
        return document(AUTHORING).section("asking the build")

    def test_the_procedure_lives_in_one_place(self):
        assert self._section()

    def test_it_names_the_command_that_answers(self):
        assert has_paragraph_with(self._section(), "validate", "--json")

    def test_it_names_the_diagnostic_for_a_value_kind(self):
        # ADR-0003: a check names the code it leans on, so an absent code can
        # downgrade the check rather than silently pass.
        assert "TSF2012" in self._section()

    def test_it_names_the_diagnostic_for_a_deprecated_verb(self):
        assert "TSF2008" in AUTHORING.read_text(encoding="utf-8")

    def test_it_says_the_offline_check_is_weaker_than_the_tenant_here(self):
        # validate warns; the push refuses. A session that reads the warning as
        # the whole answer proceeds into the refusal.
        assert has_paragraph_with(
            AUTHORING.read_text(encoding="utf-8"), "warning", "refus", "tenant"
        ), "the warning-versus-refusal split is the fact that catches people"

    def test_it_says_one_question_per_compile(self):
        assert has_paragraph_with(self._section(), "one", "question"), (
            "an oracle answers about a row; a session expecting a list will "
            "conclude the mechanism is broken"
        )


class TestTheScratchWorkspace:
    def _text(self):
        return AUTHORING.read_text(encoding="utf-8") + PROBE.read_text(encoding="utf-8")

    def test_the_markers_it_needs_are_written_down(self):
        # Three files with fabricated ids. Without them there is no workspace
        # and `validate` has nothing to read.
        body = self._text()
        assert has_paragraph_with(body, "marker", "id"), "the markers are not described"

    def test_it_is_built_outside_the_suite(self):
        assert has_paragraph_with(self._text(), "outside the suite"), (
            "a workspace inside the suite is one a later session can push"
        )

    def test_it_says_why_a_fabricated_id_is_dangerous(self):
        assert has_paragraph_with(self._text(), "push", "never"), (
            "the ids are fake by design, so what must never happen has to be "
            "said rather than left to inference"
        )

    def test_the_answer_outlives_the_workspace(self):
        assert has_paragraph_with(self._text(), "platform-facts.md", "delete") or (
            has_paragraph_with(self._text(), "platform-facts.md", "throw")
        ), "the workspace is discarded, so the answer must be recorded first"


# --- vocabulary --------------------------------------------------------------

def test_the_glossary_names_the_catalogues_declaration():
    body = CONTEXT.read_text(encoding="utf-8")
    assert "**Verb**:" in body, (
        "the documents call it a verb, a template and a step template; the "
        "glossary owns the word or all three keep circulating"
    )
    entry = body.split("**Verb**:")[1].split("_Avoid_")[0].lower()
    assert "catalogue" in entry, "a Verb is what a Catalogue declares"
    avoid = body.split("**Verb**:")[1].split("_Avoid_")[1].split("\n")[0].lower()
    assert "template" in avoid, "`template` is the spelling that keeps leaking in"


# --- the reviewable marker ---------------------------------------------------

def test_a_row_using_a_non_raw_value_carries_a_countable_marker():
    body = DIRECTORY.read_text(encoding="utf-8")
    assert has_paragraph_with(body, "`Kind:`", "expression"), (
        "the review action is 'show me every row whose value comes from "
        "somewhere else', and it needs a fixed prefix to be countable"
    )
    assert has_paragraph_with(body, "`Kind:`", "raw"), (
        "it must say which rows carry it; a marker on every row is unread"
    )


def test_the_mapping_stage_writes_the_marker():
    body = (REFERENCES_DIR.parent / "skills" / "map" / "SKILL.md").read_text(encoding="utf-8")
    assert "`Kind:`" in body, "the reference defines the marker and nothing writes it"


# --- the claim the oracle makes true ----------------------------------------

def test_checks_says_why_validity_needs_no_tenant():
    # It says Validity "needs nothing but the working copy". True only because a
    # workspace can be fabricated offline, which nothing said.
    body = CHECKS.read_text(encoding="utf-8")
    assert has_paragraph_with(body, "validity", "marker") or has_paragraph_with(
        body, "workspace", "fabricat"
    ), "Validity needs a workspace, and that it can be made without a tenant is load-bearing"
