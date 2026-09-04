"""The five checks, their fixed order, and the Check Record.

ADR-0001 fixes the order by what each check can see rather than what it costs,
which is why the expensive source comparison sits second. ADR-0003 makes the
Check Record the thing that stops a growing tool leaving silently unverified
work behind.

The failure being designed against: three clean checks that cannot see a fault
class are worse than no check, because they read as reassurance.
"""

import re

import pytest

from support import (
    MIGRATION_DIRECTORY_FILES,
    PLUGIN_ROOT,
    REFERENCES_DIR,
    command_files,
    has_paragraph_with,
    hedges_in,
    markdown_sections,
    skill_files,
)

CHECKS = REFERENCES_DIR / "checks.md"

#: The five checks in the order ADR-0001 fixes. Named here so the ordering is
#: asserted against one list rather than restated per test.
CHECK_ORDER = ("validity", "compare-to-source", "tenant", "round trip", "render")

#: The two that need a tenant. Everything before them must run offline, or the
#: check with the record of finding faults becomes the one that gets skipped.
NEEDS_A_TENANT = ("tenant", "round trip")

LOAD_BEARING = ("order", "not checked", "gains", "record")


def _text():
    return CHECKS.read_text(encoding="utf-8")


def _sections():
    return markdown_sections(_text())


def _numbered_checks(text):
    """The (number, name) pairs of a numbered list of bold-led items.

    Reading positions in the raw text was not structural enough: renumbering
    item 2 to item 6 leaves it exactly where it was in the document, so a
    position-based assertion passed with compare-to-source moved to last.
    """
    return [
        (int(number), name.lower())
        for number, name in re.findall(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*", text, re.M)
    ]


def _section(needle):
    matching = [v for k, v in _sections().items() if needle in k.lower()]
    assert len(matching) == 1, (
        f"expected exactly one section whose heading contains {needle!r}, found "
        f"{len(matching)}. Headings are: {list(_sections())}"
    )
    return matching[0]


class TestTheReferenceExists:
    def test_it_exists(self):
        assert CHECKS.is_file(), (
            "the check order is a discipline shared by two skills and a command; "
            "it needs one definition"
        )

    def test_it_opens_with_a_title(self):
        assert _text().lstrip().startswith("# ")


class TestTheFixedOrder:
    def test_all_five_checks_are_named(self):
        lowered = _section("order").lower()
        for check in CHECK_ORDER:
            assert check in lowered, f"the {check} check is not named"

    def test_they_appear_in_the_fixed_order(self):
        numbered = _numbered_checks(_section("order"))
        assert [number for number, _ in numbered] == [1, 2, 3, 4, 5], (
            f"the checks are not numbered one to five: {numbered}"
        )
        for (_, name), expected in zip(numbered, CHECK_ORDER):
            assert expected in name, (
                f"expected {expected!r} at this position, found {name!r}: {numbered}"
            )

    def test_the_order_is_numbered_so_it_cannot_be_read_as_a_set(self):
        # A bulleted list of five checks says nothing about which runs first.
        assert len(_numbered_checks(_section("order"))) == 5, (
            "the order must be a numbered list of five, not a bag of checks"
        )

    @pytest.mark.parametrize("check", NEEDS_A_TENANT)
    def test_compare_to_source_runs_before_the_checks_needing_a_tenant(self, check):
        numbered = _numbered_checks(_section("order"))
        position = {name: number for number, name in numbered}
        compare = next(n for name, n in position.items() if "compare-to-source" in name)
        needs = next(n for name, n in position.items() if check in name)
        assert compare < needs, (
            f"compare-to-source is number {compare} and {check} is {needs}; the "
            f"one check with a record of finding faults must not go last"
        )

    def test_it_says_the_order_follows_what_a_check_can_see(self):
        assert has_paragraph_with(_section("order"), "can see", "cost")

    def test_it_says_compare_to_source_needs_no_tenant(self):
        # So cheapest-first was not even buying what it appeared to buy.
        assert has_paragraph_with(_section("order"), "compare-to-source", "no tenant")

    def test_it_records_what_the_orders_evidence_was(self):
        # One scenario passed compile, preflight and a round trip and was still
        # wrong in six ways; one pass of source comparison found five.
        assert has_paragraph_with(_text(), "five of the six", "fifteen minutes")


class TestWhatTheOrderAppliesTo:
    def test_it_says_which_checks_run_against_which_kind_of_unit(self):
        # Review found this left to inference across two skills and an ADR.
        section = _section("order")
        assert has_paragraph_with(section, "compare-to-source", "distinct source step")
        assert has_paragraph_with(section, "assembled test", "between steps")


class TestAnUnrunnableCheckIsNotAPass:
    def test_it_is_recorded_as_not_checked(self):
        assert has_paragraph_with(
            _section("not checked"),
            "could not run",
            "not checked",
            absent=("treat as passed",),
        )

    def test_it_is_never_presented_as_a_pass(self):
        assert has_paragraph_with(_section("not checked"), "never", "pass")

    def test_it_says_why_a_false_pass_is_the_dangerous_direction(self):
        assert has_paragraph_with(_section("not checked"), "reassurance")


class TestWhenTheCliGainsACheck:
    def test_earlier_units_are_marked_not_checked_against_it(self):
        assert has_paragraph_with(
            _section("gains"),
            "not checked",
            absent=("inherit the pass", "assume they pass"),
        )

    def test_they_do_not_inherit_a_pass_they_never_earned(self):
        # "inherit" alone also appears in the sentence explaining why silently
        # inheriting is wrong, so the rule could be deleted and still match.
        assert has_paragraph_with(_section("gains"), "do not inherit")

    def test_re_checking_is_the_operators_costed_decision(self):
        assert has_paragraph_with(_section("gains"), "decision", "cost")

    def test_it_names_the_case_that_already_happened(self):
        # A fault class caught by a person became an automatic refusal in the
        # CLI inside about a day.
        assert has_paragraph_with(_section("gains"), "refusal", "day")

    def test_a_differing_build_is_the_signal_rather_than_a_new_flag(self):
        # The worked example was a stricter `validate`, and `validate` was in
        # the help before and after. Waiting for a new flag waits forever.
        assert has_paragraph_with(
            _section("gains"),
            "help surface",
            "differs",
            absent=("only when a new flag",),
        ), "a new check often arrives as a new rule inside an existing command"

    def test_resume_is_what_surfaces_it(self):
        assert "resume" in _section("gains").lower()


class TestTheRecord:
    def test_a_unit_of_work_is_defined_for_both_stages(self):
        section = _section("record")
        assert has_paragraph_with(section, "distinct source step", "mapping")
        assert has_paragraph_with(section, "assembled test", "assembl")

    def test_every_unit_carries_the_checks_that_ran_by_name(self):
        assert has_paragraph_with(_section("record"), "by name")

    def test_it_is_readable_without_running_anything(self):
        assert has_paragraph_with(
            _section("record"), "without running", "read"
        ), "the record must be readable rather than reconstructed"

    def test_it_names_the_cli_build_a_check_ran_under(self):
        # "build" also appears in the following sentence about a pass with no
        # build attached, which kept this green with the rule removed.
        assert has_paragraph_with(_section("record"), "build each ran under")

    def test_it_points_at_the_migration_directory_for_the_file_shape(self):
        assert "migration-directory.md" in _text()

    def test_check_record_is_one_of_the_migration_directory_files(self):
        assert "check-record.md" in MIGRATION_DIRECTORY_FILES


@pytest.mark.parametrize("section", LOAD_BEARING)
def test_no_section_grants_an_exception_to_its_own_rule(section):
    found = hedges_in(_section(section))
    assert not found, f"the '{section}' section grants an exception to its own rule: {found}"


# --- the documents that run checks -------------------------------------------

_DOCUMENTS = list(skill_files()) + list(command_files())
_IDS = lambda p: p.parent.name if p.name == "SKILL.md" else p.stem


@pytest.mark.parametrize("document", _DOCUMENTS, ids=_IDS)
def test_a_document_that_writes_the_check_record_points_at_the_check_order(document):
    body = document.read_text(encoding="utf-8")
    if "check-record.md" not in body:
        pytest.skip("this document does not write the Check Record")
    assert "references/checks.md" in body, (
        "the check order and the not-checked rule are defined in one place; a "
        "document that records a check must point there rather than restate it"
    )


def test_the_check_record_table_names_the_build_a_check_ran_under():
    # A recorded pass with no build is a pass whose meaning cannot be recovered
    # once the tool changes.
    body = (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")
    header = next(
        line for line in body.splitlines()
        if line.startswith("| Unit of Work |")
    )
    lowered = header.lower()
    assert "checks run" in lowered and "build" in lowered, header
    assert "not covered" in lowered or "not checked" in lowered, header
