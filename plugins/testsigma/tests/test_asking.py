"""The rules for raising a question, and for the two kinds of fact.

Asking is not a skill: a question arises mid-work, at the moment the information
is missing, so the discipline lives in a reference every skill points at rather
than in a stage of its own. These tests assert that reference exists, says what
it must, and that the documents which ask questions point at it.
"""

import pytest

from support import (
    COMMANDS_DIR,
    document,
    REFERENCES_DIR,
    hedges_in,
    command_files,
    has_paragraph_with,
    paragraphs,
    read_frontmatter,
    skill_files,
)

ASKING = REFERENCES_DIR / "asking.md"

DOC = document(ASKING)


def _sections():
    return DOC.sections


def _section(needle):
    return DOC.section(needle)


#: The four things an Operator must never be shown. Each is a thing they would
#: have to decode before they could answer, which makes the question unanswerable
#: by the only person who can answer it.
FORBIDDEN_IN_A_QUESTION = ("code", "file path", "stack trace", "diagnostic code")


def _body(path):
    _, body = read_frontmatter(path) if path.read_text(
        encoding="utf-8"
    ).startswith("---") else (None, path.read_text(encoding="utf-8"))
    return body


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

    def test_the_prohibition_covers_everything_put_in_front_of_them(self):
        # The scope, which the five skill copies always had and the owner never
        # did. asking.md was written about questions only, so a *report*
        # carrying a stack trace was forbidden by four skill bodies and
        # permitted by the document they cite as the rule. `survey` had already
        # invented the report-side rule itself ("Do not list paths at them"),
        # which is what an unstated scope costs.
        # "in front of them" alone is satisfied by the pre-existing line
        # "Never put any of these in front of the Operator", so asserting it
        # proved nothing. The discriminating words are the ones that widen it.
        assert has_paragraph_with(
            _section("never contain"), "not only questions"
        ), "the prohibition must say it covers more than questions"
        assert has_paragraph_with(
            _section("never contain"), "report"
        ), "and must name the case that is not a question"

    def test_the_test_is_the_decoding_burden_rather_than_the_shape_of_the_text(self):
        # Why the list is what it is. Without the reason stated, the four items
        # get read as a character-level ban, and that reading forbids
        # `survey`'s "Say which folder you chose" — a folder the Operator
        # themselves supplied, which is the one path they need no help
        # decoding.
        assert has_paragraph_with(
            _section("never contain"), "decode", "supplied"
        ), (
            "the rationale must say the test is what they would have to decode, "
            "and that naming back what they supplied is not that"
        )

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

#: The parameter is named `path`, not `document`, because `document` is the
#: handle imported above and shadowing it forced four of these tests to
#: re-implement `.flat` by hand.


def _restates_the_list(doc):
    """True where this document carries the four prohibitions itself."""
    return "stack trace" in doc.flat


@pytest.mark.parametrize("path", _DOCUMENTS, ids=_DOC_IDS)
def test_a_document_restating_the_forbidden_list_does_not_drift_from_it(path):
    # Two documents restated this list with "a command" where asking.md says
    # "code" — narrower, and wrong: a shell command is not the concern, source
    # identifiers are. A partial restatement is how one definition becomes two.
    doc = document(path)
    if not _restates_the_list(doc):
        pytest.skip("this document does not restate what a question may not contain")
    for forbidden in FORBIDDEN_IN_A_QUESTION:
        assert forbidden in doc.flat, (
            f"this document restates the forbidden list but omits {forbidden!r}"
        )
    assert "references/asking.md" in doc.text, (
        "a document restating the list must point at the definition it restates"
    )


@pytest.mark.parametrize("path", _DOCUMENTS, ids=_DOC_IDS)
def test_a_document_restating_the_list_does_not_deny_restating_it(path):
    # Four documents restated the four prohibitions and then said "this does
    # not restate it". The copy is deliberate — a skill body loads whole on
    # trigger, so the constraint is in context when a question arises mid-work,
    # where a reference one hop away would not be — but a sentence claiming the
    # rule is not where it plainly is stops a reader trusting either copy.
    doc = document(path)
    if not _restates_the_list(doc):
        pytest.skip("this document does not restate what a question may not contain")
    # Paragraph-scoped, not document-scoped. Two paragraphs of `assemble`
    # honestly say a *different* rule is not restated there — the placeholder
    # prohibition and the step-order arithmetic — and both are correct. Only
    # the paragraph carrying these four prohibitions may not deny carrying
    # them. "does not restate" subsumes "this does not restate", so two
    # needles cover what three did.
    carrying = [
        " ".join(para.split()).lower()
        for para in paragraphs(doc.body)
        if "stack trace" in para.lower()
    ]
    assert carrying, "the list is in this document but in no single paragraph"
    for para in carrying:
        for denial in ("does not restate", "not restated here"):
            assert denial not in para, (
                f"this paragraph restates the list and then denies it with "
                f"{denial!r}; the copy is fine, the denial is not"
            )


@pytest.mark.parametrize("path", _DOCUMENTS, ids=_DOC_IDS)
def test_a_copy_says_why_it_is_a_copy(path):
    # An unexplained copy invites the deletion an architecture review already
    # proposed for these five. The reason is load-bearing: a skill body loads
    # whole on trigger, so the constraint is in context when a question arises
    # mid-work, where a reference one seam away would not be. Nothing tested
    # this claim, and rewording one copy's reason to "because it reads better
    # that way" left the whole suite green.
    doc = document(path)
    if not _restates_the_list(doc):
        pytest.skip("this document does not restate what a question may not contain")
    assert "mid-work" in doc.flat, (
        "the copy must say why it is copied rather than pointed at, or a later "
        "reader removes it as duplication"
    )


@pytest.mark.parametrize("path", _DOCUMENTS, ids=_DOC_IDS)
def test_a_copy_does_not_describe_the_owner_as_narrower_than_it_is(path):
    # The defect that caused all of this. Five documents forbade code, paths,
    # traces and diagnostic codes in anything put in front of the Operator,
    # then cited asking.md as "the rule for what a question may contain" — a
    # narrower document than the rule they were stating. The scope is now in
    # asking.md, so a copy attributing the narrow version to it is stale.
    doc = document(path)
    if not _restates_the_list(doc):
        pytest.skip("this document does not restate what a question may not contain")
    assert "rule for what a question may contain" not in doc.flat, (
        "asking.md covers everything shown to the Operator, not only "
        "questions; a copy must not describe it as the narrower rule"
    )


@pytest.mark.parametrize("path", _DOCUMENTS, ids=_DOC_IDS)
def test_a_document_that_touches_open_questions_points_at_the_asking_rules(path):
    doc = document(path)
    if "open-questions.md" not in doc.text:
        pytest.skip("this document does not touch open questions")
    assert "references/asking.md" in doc.text, (
        "the rules for raising a question are defined in one place; a document "
        "that raises or reports one must point at them rather than restate them"
    )


def test_a_partial_directory_is_reported_as_a_missing_record_not_a_filename():
    # The violation the widened scope created. `resume` said "if a file the
    # reference names is missing, say which and stop" — a bare filename put in
    # front of the Operator, and one they did not supply, so the
    # decoding-burden carve-out does not reach it. The Operator needs to know
    # which *record* is missing, which the glossary already names.
    resume = document(COMMANDS_DIR / "resume.md")
    carrying = [
        " ".join(para.split()).lower()
        for para in paragraphs(resume.body)
        if "partial directory" in para.lower()
    ]
    assert len(carrying) == 1, f"expected one paragraph on a partial directory, got {len(carrying)}"
    para = carrying[0]
    assert "say which and stop" not in para, (
        "naming the missing file to the Operator is the thing asking.md now "
        "forbids everywhere, not only in questions"
    )
    assert "record" in para, (
        "it must name what is missing in the Operator's terms instead"
    )
