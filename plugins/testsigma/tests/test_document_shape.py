"""A document's order, which no other control in this suite can see.

Every other test reads sections by name, so a section in the wrong *place*
passes all of them. That is not hypothetical: `map`'s "Before a row is
proposed" gate was written as the 9th of 11 sections, between Step 6 and Step
7, constraining something a reader had already done two steps earlier. It
survived two full diff reviews, because a diff shows a section's text and not
its position.

So these tests assert shape: that numbered steps run in order, and that a gate
sits before what it gates.
"""

import re

import pytest

from support import (
    COMMANDS_DIR,
    doc_id,
    document_files,
    SKILLS_DIR,
    document,
    preamble,
    skill_files,
)

DOCUMENTS = document_files()


#: An unnumbered gate that legitimately sits after a numbered step, with the
#: reason. `survey` checks four refusals against the suite root, so it cannot
#: check them until Step 0 has established which folder that is — the gate is
#: correctly second. Anything not listed here is a misplacement.
GATES_AFTER_A_STEP = {
    ("survey", "Before anything else: four refusals"),
}

_NUMBERED = re.compile(r"^Step (\d+):")


def _headings(path):
    return list(document(path).sections)


@pytest.mark.parametrize("path", DOCUMENTS, ids=doc_id)
def test_numbered_steps_run_in_order_without_gaps(path):
    numbers = [
        int(match.group(1))
        for match in (_NUMBERED.match(h) for h in _headings(path))
        if match
    ]
    if not numbers:
        pytest.skip("this document has no numbered steps")
    assert numbers == sorted(numbers), f"steps are out of order: {numbers}"
    assert len(numbers) == len(set(numbers)), f"a step number is used twice: {numbers}"
    assert numbers == list(range(numbers[0], numbers[0] + len(numbers))), (
        f"the step numbers skip: {numbers}"
    )


@pytest.mark.parametrize("path", DOCUMENTS, ids=doc_id)
def test_an_unnumbered_gate_comes_before_the_steps_it_gates(path):
    # A gate reached after the work it constrains is worse than a missing one:
    # the reader has already acted, and the gate reads as a summary of what
    # they did rather than a condition on it.
    headings = _headings(path)
    numbered = [bool(_NUMBERED.match(h)) for h in headings]
    if not any(numbered):
        pytest.skip("this document has no numbered steps")
    # Between two numbered steps, not merely after the first. A closing
    # section that follows the last step is a legitimate shape — the rule is
    # about a gate a reader reaches after acting on what it gates.
    first_step = numbered.index(True)
    last_step = len(numbered) - 1 - numbered[::-1].index(True)
    misplaced = [
        heading
        for index, heading in enumerate(headings)
        if first_step < index < last_step
        and not numbered[index]
        and (doc_id(path), heading) not in GATES_AFTER_A_STEP
    ]
    assert not misplaced, (
        f"these unnumbered sections sit among the numbered steps, so a reader "
        f"working in order meets them after the point they constrain: "
        f"{misplaced}. If one belongs there, add it to GATES_AFTER_A_STEP with "
        f"the reason."
    )


# --- cross-references point at the right place -------------------------------


def test_resume_cites_the_step_that_actually_writes():
    # An off-by-one cross-reference. The preamble said "except the one case
    # Step 2 names", and the write is specified in Step 1 — Step 2 only names
    # the active Phase. Nothing in this suite could see it, because every
    # control reads a section by name and none reads what a section claims
    # about another.
    resume = document(COMMANDS_DIR / "resume.md")
    writing = [
        heading
        for heading, body in resume.sections.items()
        if "the one write this command makes" in " ".join(body.split()).lower()
    ]
    assert len(writing) == 1, (
        f"expected exactly one section to claim the single write, found {writing}"
    )
    step = _NUMBERED.match(writing[0])
    assert step, f"the writing section is not a numbered step: {writing[0]!r}"
    cited = re.findall(r"step (\d+) names", " ".join(preamble(resume.body).split()).lower())
    assert cited == [step.group(1)], (
        f"the preamble cites Step {cited} as the one that writes, but the write "
        f"is specified in Step {step.group(1)}"
    )


def test_no_skill_tells_the_agent_to_run_a_slash_command():
    # `resume` is an Operator surface. A stage that reaches for it couples
    # itself to a UI affordance instead of naming the action, and the agent
    # cannot invoke it on the Operator's behalf anyway.
    offenders = []
    for path in sorted(skill_files()):
        flat = document(path).flat
        for phrase in ("run the resume command", "run the survey command", "run /resume"):
            if phrase in flat:
                offenders.append(f"{doc_id(path)}: {phrase!r}")
    assert not offenders, f"skills instructing the agent to run a command: {offenders}"


# --- descriptions route a request to one skill -------------------------------


def _description(path):
    return " ".join(str(document(path).meta.get("description", "")).split()).lower()


def _examples(description):
    """The em-dash-delimited list of source formats a description offers."""
    parts = description.split("—")
    if len(parts) < 3:
        return set()
    return {
        item.strip()
        for item in parts[1].split(",")
        if item.strip() and "any " not in item
    }


def test_a_format_named_by_two_skills_carries_each_skill_s_discriminator():
    # "an ALM design-step export" appears in two descriptions, and both are
    # true of it: an ALM export genuinely carries no locators *and* has no
    # adapter shipped. So the example cannot be removed from either. What
    # decides between them is which of the two things is missing, and that has
    # to be in the description a request is matched against.
    resolve = _description(SKILLS_DIR / "resolve-elements" / "SKILL.md")
    adapter = _description(SKILLS_DIR / "write-an-adapter" / "SKILL.md")
    # Computed rather than keyed on "ALM": naming the example meant the test
    # passed vacuously the moment the example was reworded, describing a
    # collision that no longer existed.
    shared = _examples(resolve) & _examples(adapter)
    assert shared, (
        "these two descriptions no longer share a format example; if that is "
        "deliberate this test has nothing left to guard and should go"
    )
    assert "adapter" in resolve and (
        "already" in resolve or "existing adapter" in resolve
    ), "resolve-elements runs where an adapter exists; its description must say so"
    assert "no source adapter" in adapter or "not covered" in adapter, (
        "write-an-adapter runs where no adapter exists; its description must say so"
    )


def test_assemble_does_not_offer_itself_for_a_cold_start():
    # "converting a feature file's tests" is a plausible first request from
    # someone with no Migration at all, and a trailing qualifier is the
    # weakest place to put the precondition. survey owns the cold start.
    # Two earlier cuts of this test were vacuous. Asserting the absence of one
    # 47-character string passed on any reword. Asserting that "reviewed"
    # precedes "feature file" passed on the original defect too, because the
    # opening clause always carried the precondition — what a cold start
    # matches on is the *example*, and the example is what has to be
    # qualified. So the clause offering a feature file must carry the
    # precondition itself.
    assemble = _description(SKILLS_DIR / "assemble" / "SKILL.md")
    clauses = [c for c in re.split(r"[,—]", assemble) if "feature file" in c]
    assert clauses, "the description no longer offers a feature file as a trigger"
    for clause in clauses:
        assert "reviewed" in clause or "already" in clause, (
            f"the clause offering a feature file carries no precondition, so a "
            f"cold-start request matches it: {clause.strip()!r}"
        )
    assert "survey" in assemble, (
        "and the description must name where a cold-start request belongs"
    )


def test_the_slot_rule_sits_inside_the_step_that_defines_a_row():
    # The instance the class control above no longer sees. The slot rule was a
    # top-level gate placed 9th of 11, after Step 6, constraining the
    # Expression cell a reader had filled in four steps earlier. It is now a
    # subsection of Step 2, where a row's columns are established, so it
    # cannot be reached after what it gates — but that also folds it into Step
    # 2's body, out of reach of a control that reads `##` headings. This is
    # what keeps the fix from silently coming undone.
    step_two = document(SKILLS_DIR / "map" / "SKILL.md").section("step 2")
    flat = " ".join(step_two.split()).lower()
    assert "slot decides the value" in flat, (
        "the slot rule has moved back out of Step 2; if it is a top-level "
        "section again it is a gate a reader meets after using it"
    )
    assert "`kind:`" in flat, "and the marker it mandates belongs with it"
