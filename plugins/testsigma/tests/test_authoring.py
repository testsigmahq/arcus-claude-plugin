"""The target-side rules: what the validator and the push refuse.

Everything else in references/ is about reading a source. These rules were
established by authoring a real conversion and pushing it to a tenant, which is
the only way most of them surface.

They are observations of one CLI build against one tenant, so the reference says
to re-probe rather than assume — ADR-0003.
"""

import pytest

from support import (
    REFERENCES_DIR,
    command_files,
    has_paragraph_with,
    hedges_in,
    markdown_sections,
    preamble,
    skill_files,
)

AUTHORING = REFERENCES_DIR / "authoring.md"

LOAD_BEARING = ("deprecated", "layout", "round trip", "unconverted region", "credential")


def _text():
    return AUTHORING.read_text(encoding="utf-8")


def _section(needle):
    sections = markdown_sections(_text())
    matching = [v for k, v in sections.items() if needle in k.lower()]
    assert len(matching) == 1, (
        f"expected one section containing {needle!r}, found {len(matching)}: "
        f"{list(sections)}"
    )
    return matching[0]


def test_it_exists():
    assert AUTHORING.is_file(), (
        "nothing covered writing the target correctly; every other reference "
        "reads the source"
    )


def test_it_says_to_re_probe_rather_than_trust_these():
    # One build, one tenant. ADR-0003 says probe and never pin.
    assert has_paragraph_with(_text(), "re-probe", "one cli build")


def test_diagnostic_codes_stay_out_of_the_operators_view():
    assert has_paragraph_with(_text(), "diagnostic codes", "never spoken")


class TestADeprecatedTemplateIsAnError:
    def test_it_is_an_error_and_not_a_warning(self):
        assert has_paragraph_with(
            _section("deprecated"),
            "may not use it",
            absent=("only a warning",),
        ), "the push refuses the create outright"

    def test_it_explains_why_deprecated_reads_as_safe(self):
        # True for steps that already exist, false for anything created.
        assert has_paragraph_with(_section("deprecated"), "not removed", "create")

    def test_a_replacement_is_carried_rather_than_found_at_push_time(self):
        assert has_paragraph_with(_section("deprecated"), "replacement", "authoring error")

    def test_a_verb_is_not_chosen_by_its_name(self):
        # One verb reading as clicking text is OCR-based: screenshot, extract,
        # click a coordinate. Nothing in the name says so.
        assert has_paragraph_with(
            _section("deprecated"), "ocr", absent=("trust the name",)
        )


class TestWhatTheValidatorEnforces:
    def test_environment_names_use_bracket_lookup_always(self):
        assert has_paragraph_with(
            _section("layout"), "bracket form always", "identifier-safe"
        ), "dotted access working for some names is the trap"

    def test_environments_are_project_scoped(self):
        assert has_paragraph_with(_section("layout"), "project-scoped")

    def test_attach_takes_positional_arguments(self):
        assert has_paragraph_with(_section("layout"), "positional")

    def test_there_is_no_formatter_and_canonical_text_comes_from_a_pull(self):
        assert has_paragraph_with(_section("layout"), "no formatter", "pull --write")


class TestTheFirstPushAndTheRoundTrip:
    def test_server_materialised_defaults_are_adopted_by_pulling(self):
        assert has_paragraph_with(_section("first push"), "pull --write", "first")

    def test_a_write_count_is_not_evidence_of_a_push(self):
        # Entity-level operations, unrelated to the number of steps.
        assert has_paragraph_with(_section("round trip"), "entity-level")

    def test_the_round_trip_is_what_confirms_it(self):
        assert has_paragraph_with(
            _section("round trip"),
            "no difference",
            absent=("the count confirms",),
        )


class TestADeclinedRegionIsVisible:
    def test_an_empty_named_block_marks_it(self):
        assert has_paragraph_with(_section("unconverted region"), "empty inline block")

    def test_residue_has_somewhere_to_point(self):
        assert has_paragraph_with(_section("unconverted region"), "residue")

    def test_steps_are_neither_dropped_nor_commented(self):
        assert has_paragraph_with(
            _section("unconverted region"), "do not drop", "comment"
        ), "a comment is invisible in the tenant"


class TestApiBlocksOverturnAResidueCause:
    def test_the_json_assertion_cause_is_overturned(self):
        section = _section("residue cause overturned")
        assert has_paragraph_with(section, "bodypath", "expresses it directly")

    def test_it_says_what_the_entry_was_right_and_wrong_about(self):
        # Right about the web catalogue, wrong about the format. This is what
        # Residue's reasoning field exists for.
        assert has_paragraph_with(
            _section("residue cause overturned"), "right about", "wrong about"
        )

    def test_the_consequence_is_stated_in_scenarios(self):
        assert has_paragraph_with(_section("residue cause overturned"), "28 of 35")


class TestCredentialsFoundInASource:
    def test_a_value_is_never_inlined(self):
        assert has_paragraph_with(
            _section("credential"),
            "never inline",
            absent=("inline it if",),
        )

    def test_it_is_routed_to_an_environment_variable(self):
        assert has_paragraph_with(_section("credential"), "environment variable", "tenant")

    def test_the_operator_is_told_to_rotate_it(self):
        assert has_paragraph_with(_section("credential"), "rotated", "theirs to act on")

    def test_the_value_is_never_written_anywhere(self):
        assert has_paragraph_with(
            _section("credential"), "never copy the value", "commit message"
        )


@pytest.mark.parametrize("section", LOAD_BEARING)
def test_no_section_grants_an_exception_to_its_own_rule(section):
    found = hedges_in(_section(section))
    assert not found, f"the '{section}' section grants an exception: {found}"


def test_its_preamble_grants_no_exception():
    assert not hedges_in(preamble(_text()))


def test_the_skill_that_writes_the_target_points_at_it():
    assemble = next(s for s in skill_files() if s.parent.name == "assemble")
    assert "references/authoring.md" in assemble.read_text(encoding="utf-8"), (
        "assembly is what writes the target; it must follow these rules"
    )
