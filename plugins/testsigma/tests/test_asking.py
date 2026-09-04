"""The rules for raising a question, and for the two kinds of fact.

Asking is not a skill: a question arises mid-work, at the moment the information
is missing, so the discipline lives in a reference every skill points at rather
than in a stage of its own. These tests assert that reference exists, says what
it must, and that the documents which ask questions point at it.
"""

import pytest

from support import (
    REFERENCES_DIR,
    hedges_in,
    command_files,
    has_paragraph_with,
    markdown_sections,
    read_frontmatter,
    skill_files,
)

ASKING = REFERENCES_DIR / "asking.md"

#: The four things an Operator must never be shown. Each is a thing they would
#: have to decode before they could answer, which makes the question unanswerable
#: by the only person who can answer it.
FORBIDDEN_IN_A_QUESTION = ("code", "file path", "stack trace", "diagnostic code")


def _body(path):
    _, body = read_frontmatter(path) if path.read_text(
        encoding="utf-8"
    ).startswith("---") else (None, path.read_text(encoding="utf-8"))
    return body


def _sections():
    return markdown_sections(ASKING.read_text(encoding="utf-8"))


def _prohibited_list():
    """The bulleted list of what a question may never contain, lowercased."""
    section = _section("never contain")
    from support import paragraphs

    lists = [
        block
        for block in paragraphs(section)
        if all(line.startswith("- ") for line in block.splitlines() if line.strip())
    ]
    assert len(lists) == 1, (
        f"expected one bulleted prohibition, found {len(lists)}"
    )
    return lists[0].lower()


def _section(needle):
    matching = [v for k, v in _sections().items() if needle in k.lower()]
    assert len(matching) == 1, (
        f"expected exactly one section whose heading contains {needle!r}, found "
        f"{len(matching)}. Headings are: {list(_sections())}"
    )
    return matching[0]


class TestTheAskingReferenceExists:
    def test_it_exists(self):
        assert ASKING.is_file(), (
            "asking is not a skill, so the discipline needs a document of its own"
        )

    def test_no_skill_exists_whose_job_is_asking(self):
        # A question arises mid-work. A skill for asking would mean handing off
        # at the moment the information is missing, which is the moment it is
        # cheapest to ask.
        names = [skill.parent.name for skill in skill_files()]
        for name in names:
            assert "question" not in name and "ask" not in name, (
                f"{name} looks like a skill for asking; asking is not a stage"
            )


#: The sections that state absolute rules. A paragraph granting an exception
#: anywhere in one of these guts the rule while leaving its sentence intact.
LOAD_BEARING = ("raise", "admissible", "never contain", "answer", "record", "fact")


@pytest.mark.parametrize("section", LOAD_BEARING)
def test_no_section_grants_an_exception_to_its_own_rule(section):
    # Section-wide, unlike every other assertion in this file, which is what
    # makes it able to see an added contradiction. A review demonstrated four
    # walk-backs at once — "reasonable to strike it without waiting", "a nicety
    # rather than a requirement", "should simply be shown it", "either file is
    # acceptable" — each keeping the correct paragraph and each passing.
    found = hedges_in(_section(section))
    assert not found, (
        f"the '{section}' section grants an exception to its own rule: {found}"
    )


class TestWhatMakesAQuestionAdmissible:
    def test_a_question_may_be_raised_mid_work_without_handing_off(self):
        assert has_paragraph_with(_section("raise"), "any skill", "without")

    def test_the_admissibility_test_is_stated(self):
        # The single test that decides whether a question may be put at all.
        assert has_paragraph_with(
            _section("admissible"), "application open", "no code checked out"
        ), "the admissibility test must be stated as a test, not implied"

    @pytest.mark.parametrize("forbidden", FORBIDDEN_IN_A_QUESTION)
    def test_it_forbids_each_thing_an_operator_would_have_to_decode(self, forbidden):
        # Scoped to the bulleted prohibition rather than the section. Every one
        # of these words also appears in the paragraph saying where the detail
        # goes instead, so section-presence passed with a bullet deleted.
        assert forbidden in _prohibited_list(), (
            f"a question may never contain a {forbidden}, and the list does not say so"
        )

    def test_the_prohibition_is_a_prohibition(self):
        assert has_paragraph_with(
            _section("never contain"),
            "never",
            absent=("where helpful", "unless the operator", "it is fine to include"),
        )

    def test_a_forbidden_detail_goes_to_the_migration_directory_rather_than_vanishing(self):
        # The rule is where it goes, not that it is deleted. A diagnostic code
        # an Operator must not see is still a fact the Migration needs.
        assert has_paragraph_with(_section("never contain"), "migration directory")

    def test_a_question_offers_a_short_list_of_answers(self):
        assert has_paragraph_with(_section("answer"), "short list")

    def test_one_of_those_answers_is_recommended(self):
        assert has_paragraph_with(
            _section("answer"),
            "recommend",
            absent=("do not recommend", "never recommend"),
        ), "an Operator asked to compose an answer from nothing is being asked to work"

    def test_the_recommendation_carries_its_reason(self):
        # A recommendation an Operator cannot check is a decision taken for them.
        assert has_paragraph_with(_section("answer"), "recommend", "why")


class TestWhatKeepsAQuestionOpen:
    def test_it_is_recorded_at_the_moment_it_is_raised(self):
        assert has_paragraph_with(
            _section("record"), "open-questions.md", "moment"
        ), "a question recorded later is a question that can be forgotten first"

    def test_only_an_answer_clears_it(self):
        assert has_paragraph_with(
            _section("record"),
            "only an answer clears",
            absent=("may be cleared when",),
        ), "anything else that clears a question is how one goes quiet"

    def test_it_survives_the_session_that_raised_it(self):
        assert has_paragraph_with(_section("record"), "session")

    def test_it_names_the_failure_it_exists_to_prevent(self):
        # It has already happened: a question was asked once, never answered,
        # and nothing anywhere recorded that it was still open.
        body = ASKING.read_text(encoding="utf-8")
        assert has_paragraph_with(body, "never answered", "nothing")


class TestTheTwoKindsOfFact:
    def test_the_two_kinds_are_kept_apart(self):
        section = _section("fact")
        assert "platform-facts.md" in section and "application-facts.md" in section

    def test_a_platform_fact_is_settled_by_probing_rather_than_by_asking(self):
        assert has_paragraph_with(
            _section("fact"),
            "platform fact",
            "probing",
            "rather than",
        ), "the Operator must only be asked what only they can answer"

    def test_an_application_fact_stays_open_until_answered(self):
        assert has_paragraph_with(_section("fact"), "application fact", "until")

    def test_the_distinction_is_who_can_answer(self):
        assert has_paragraph_with(_section("fact"), "who can answer")

    def test_it_points_at_the_migration_directory_definition(self):
        assert "references/migration-directory.md" in ASKING.read_text(
            encoding="utf-8"
        ) or "migration-directory.md" in ASKING.read_text(encoding="utf-8")


# --- the documents that ask ---------------------------------------------------

_DOCUMENTS = list(skill_files()) + list(command_files())
_DOC_IDS = lambda p: p.parent.name if p.name == "SKILL.md" else p.stem


@pytest.mark.parametrize("document", _DOCUMENTS, ids=_DOC_IDS)
def test_a_document_restating_the_forbidden_list_does_not_drift_from_it(document):
    # Two documents restated this list with "a command" where asking.md says
    # "code" — narrower, and wrong: a shell command is not the concern, source
    # identifiers are. A partial restatement is how one definition becomes two.
    body = document.read_text(encoding="utf-8")
    if "stack trace" not in body:
        pytest.skip("this document does not restate what a question may not contain")
    for forbidden in FORBIDDEN_IN_A_QUESTION:
        assert forbidden in body.lower(), (
            f"this document restates the forbidden list but omits {forbidden!r}"
        )
    assert "references/asking.md" in body, (
        "a document restating the list must point at the definition it restates"
    )


@pytest.mark.parametrize("document", _DOCUMENTS, ids=_DOC_IDS)
def test_a_document_that_touches_open_questions_points_at_the_asking_rules(document):
    body = document.read_text(encoding="utf-8")
    if "open-questions.md" not in body:
        pytest.skip("this document does not touch open questions")
    assert "references/asking.md" in body, (
        "the rules for raising a question are defined in one place; a document "
        "that raises or reports one must point at them rather than restate them"
    )
