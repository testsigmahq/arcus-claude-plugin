"""The target-side rules: what the validator and the push refuse.

Everything else in references/ is about reading a source. These rules were
established by authoring a real conversion and pushing it to a tenant, which is
the only way most of them surface.

They are observations of one CLI build against one tenant, so the reference says
to re-probe rather than assume — ADR-0003.
"""

import pytest

from support import (
    document,
    REFERENCES_DIR,
    has_paragraph_with,
    hedges_in,
    preamble,
    skill_files,
)

AUTHORING = REFERENCES_DIR / "authoring.md"

DOC = document(AUTHORING)


def _text():
    return DOC.body


def _section(needle):
    return DOC.section(needle)


LOAD_BEARING = ("deprecated", "layout", "round trip", "unconverted region", "credential")


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


# --- value kinds -------------------------------------------------------------
#
# A slot's `allowedTypes` decides whether it will accept a literal, a data
# profile column, a runtime variable, a global, a generator or an upload path.
# That is what makes a mapping legal or illegal, and the plugin had no term for
# it, so a row could propose a value the slot would never take and nothing
# before the push would say so.

class TestValueKinds:
    def _kinds(self):
        return _section("value kind")

    def test_the_reference_has_a_section_for_them(self):
        assert self._kinds()

    def test_the_slot_decides_and_not_the_verb(self):
        assert has_paragraph_with(self._kinds(), "slot", "allowedtypes")

    def test_it_gives_the_spelling_of_each_kind(self):
        # Without the spellings the concept cannot be applied to a row: the kind
        # a value has is a consequence of how it is written.
        body = self._kinds().lower()
        for spelling in ("param", "runtime", "env", "upload", "random"):
            assert spelling in body, f"no spelling given for the {spelling} kind"

    def test_it_says_what_an_unacceptable_kind_makes_the_row(self):
        assert has_paragraph_with(self._kinds(), "residue", "kind"), (
            "a value no allowed kind can carry has an outcome, and it is not "
            "left to the author to invent one"
        )

    def test_it_points_at_the_catalogue_rather_than_copying_it(self):
        # Retired finding 1: a hand-copied duplicate of a generated file is
        # exactly the staleness this plugin warns about.
        assert has_paragraph_with(
            self._kinds(),
            "generator",
            absent=("the full list is", "listed below", "every generator is"),
        )
        assert not any(
            line.strip().startswith("- `gen.") for line in self._kinds().splitlines()
        ), "the generators are being copied into the plugin"


def test_deprecation_is_established_before_a_row_is_proposed():
    # It was learned from a failed push, and a third of the web surface carries
    # it, so discovering it at push time is a choice rather than a necessity.
    # This test previously asserted the field was "readable" from the schema.
    # It is not, from an installed build: the mechanism is a compile and a named
    # diagnostic, per ADR-0006.
    section = _section("deprecated")
    assert has_paragraph_with(section, "before authoring", "compile"), (
        "the rule says treat it as an authoring error, but never how to know"
    )
    assert "TSF2008" in section, (
        "ADR-0003 requires the code a check leans on to be named where the "
        "rule is stated"
    )
    assert "third" in section or "158" in section, (
        "the scale is what makes this worth establishing rather than meeting"
    )


class TestTheUnconvertedMarkerCarriesItsReason:
    """An empty block is only useful if its label says what was needed.

    The block validates and shows in the tenant either way, so a label reading
    `Not converted` produces a marker that is present, correct, and useless: the
    reader learns a step is missing and nothing about what would restore it. The
    marker's whole payload is its label.
    """

    def _section(self):
        # Normalised: every phrase below straddles a line wrap in the source,
        # which is the failure mode `Document.flat` was added for.
        return " ".join(DOC.section("marker").split()).lower()

    def test_the_label_names_what_was_needed(self):
        section = self._section()
        assert "what was needed" in section or "names the work" in section, (
            "a label that only announces an absence gives a reader nothing to "
            "act on"
        )

    def test_it_says_where_the_marker_goes(self):
        assert "where the step would have gone" in self._section(), (
            "position is the one thing a marker carries that the Migration "
            "Directory cannot"
        )

    def test_the_marker_and_the_residue_entry_are_both_required(self):
        section = self._section()
        assert "not a substitute" in section, (
            "either alone leaves a gap nobody can find, or one nobody can "
            "explain"
        )


class TestTheApiGrammarIsProbedNotGuessed:
    """The api block's spellings are not guessable, and were guessed.

    Measured on a clean-room conversion before `list blocks` existed: 18
    brute-force loops piping candidate spellings through `validate`, 274 tool
    calls, no test. `verify` conditions are named arguments rather than calls —
    `status(equals = 200)`, not `verifyStatusCode(200)` — and `verify body`
    takes at most one of path/file/storedObject, which nothing in the prose
    implies. ADR-0009 carries the reasoning.
    """

    def _section(self):
        return " ".join(DOC.section("api block").split())

    def test_it_names_the_probe(self):
        assert "list blocks --kind api" in self._section(), (
            "prose about what an api block can do, with no way to learn how to "
            "spell it, is what produced the guessing"
        )

    def test_it_shows_that_a_condition_is_a_named_argument(self):
        assert "status(equals = 200)" in self._section(), (
            "the shape a reader would never guess is worth one example, since "
            "it is the one the measured run got wrong"
        )

    def test_it_defers_the_reasoning_to_the_decision(self):
        assert "ADR-0009" in self._section()


class TestTheWorkspaceLayoutIsAsked:
    """The layout is asked for, not transcribed.

    It was written down here for one commit, deliberately and marked interim,
    because a clean-room run brute-forced directory names with no probe and no
    documentation to go on. `testsigma list layout` now projects it from the
    same table the walk enforces, so the copy is deleted — which is the whole
    shape ADR-0009 describes: write down what cannot be asked, and delete it
    when it can.
    """

    def _section(self):
        return " ".join(DOC.section("values, names and layout").split())

    def test_it_names_the_probe(self):
        assert "testsigma list layout" in self._section(), (
            "without the probe named, the layout is undiscoverable again and "
            "the next run guesses directory names"
        )

    def test_it_does_not_transcribe_the_map(self):
        # The failure this guards is a well-meant re-add. A transcribed map
        # goes stale silently, and a stale map is worse than no map because it
        # is consulted instead of the probe.
        section = self._section()
        transcribed = sum(
            1 for path in ("tests/<folder>/*.test.sigma",
                           "stepGroups/<folder>/*.stepGroup.sigma",
                           "tdps/<folder>/*.tdp.sigma",
                           "uploads/*.upload.sigma")
            if path in section
        )
        assert transcribed == 0, (
            "the map is back in the reference; name the probe instead"
        )

    def test_it_keeps_the_one_fact_the_probe_does_not_volunteer(self):
        # `list layout` reports `elements` for a `screen`, but nothing tells a
        # reader that the directory and the entity disagree on purpose. That is
        # the trip hazard, and it costs a cycle every time it is hit.
        section = self._section()
        assert "a `screen` lives in `elements/`" in section

    def test_it_says_which_field_to_read_from_json(self):
        assert "`path`" in self._section(), (
            "the four component fields are there to be assembled wrongly"
        )


class TestProbingIsNonDestructive:
    """Guessing costs a validate; guessing by deleting costs the work.

    A measured run brute-forced the elements directory with
    `for dir in screens Screens elements …; do rm -rf "$dir"; done`, inside the
    Operator's repository, over files an earlier stage had written. The layout
    being undocumented explains the guessing. It does not explain the `rm -rf`,
    and documenting the layout would not have prevented the next one.
    """

    def _section(self):
        return " ".join(DOC.section("values, names and layout").split()).lower()

    def test_it_forbids_deleting_to_probe(self):
        section = self._section()
        assert "never by deleting" in section, (
            "an agent establishing a convention will experiment; the rule has "
            "to say which direction is safe"
        )

    def test_it_says_what_to_do_instead(self):
        assert "write one candidate file" in self._section()

    def test_it_extends_the_rule_to_the_tenant(self):
        # The same reasoning, and the more expensive half: a push is not offline
        # and not undoable the way a local file is.
        assert "never by pushing" in self._section()


class TestInterpolationIsBoundedAndSaysWhere:
    """One example of interpolation, with no statement of where it is legal.

    The reference showed `"${env[\\"API_BASE_URL\\"]}/path"` under a rule about
    bracket lookup and said "including inside interpolation" — true of that
    slot, and readable as licence for any slot. A measured run wrote
    `storeValue("SRL080${random(4)}", …)`, which compiled and was refused at the
    wire. The CLI's own tour taught the same spelling, so the shape was not this
    plugin's invention; the omission that let it through was.
    """

    def _section(self):
        return " ".join(DOC.section("values, names and layout").split())

    def test_it_says_where_interpolation_is_legal(self):
        section = self._section()
        assert "TSF2013" in section
        for legal in ("url", "raw body", "generator argument"):
            assert legal in section, f"{legal} is not named as a place it works"

    def test_it_says_a_value_slot_is_not_one_of_them(self):
        assert "value slot is not one of" in self._section().lower()

    def test_it_explains_why_bare_passes_and_interpolated_does_not(self):
        # Without the reason this reads as an arbitrary prohibition, and an
        # arbitrary prohibition is one an agent works around.
        section = self._section()
        assert "kind column" in section

    def test_it_does_not_blame_generators(self):
        # The narrow reading — "generators cannot appear in strings" — was mine,
        # and it is wrong: `"x${param.prefix}"` fails the same way.
        assert "param.prefix" in self._section(), (
            "the non-generator counterexample is what stops the rule being "
            "remembered as a fact about generators"
        )

    def test_it_gives_the_unique_id_recipe(self):
        section = self._section()
        assert "whole value" in section.lower()
        assert "runtime variable" in section

    def test_dropping_the_prefix_is_named_as_a_concession(self):
        # The measured run recovered by deleting the prefix, which changes the
        # value the test produces. Recorded it is a Concession; unrecorded it is
        # a Divergence, and nothing else separates them.
        assert "Concession" in self._section()


class TestDynamicLocatorsAreVerbSelected:
    """The obvious wrong turning is documented, because a run took it.

    `element.dynamic` exists and is a flag on a stored element. It is not a
    step-side parameter mechanism, and there is no placeholder binding at all —
    a run guessed seven names for one, then wrote a locator with a `{value}`
    hole beside `dynamic = true`, producing a file that validates and does not
    do what it appears to.
    """

    def _section(self):
        return " ".join(DOC.section("values, names and layout").split())

    def test_it_says_the_verb_carries_one_of_the_locators(self):
        assert "Verb-selected" in self._section()

    def test_it_names_the_probe_that_proves_no_binding_exists(self):
        # Without this the reader cannot distinguish "no such binding" from "a
        # name nobody has guessed yet", which is what made the search unbounded.
        assert "list blocks --kind step" in self._section()

    def test_it_gives_both_shapes(self):
        section = self._section()
        assert "Verb-selected" in section
        assert "stored element carrying a parameter reference" in section

    def test_it_shows_the_example_in_the_spelling_that_compiles(self):
        # The worked element carried the sigil while the prose said to write the
        # format spelling. An example contradicting its own rule is the half a
        # reader copies.
        section = self._section()
        assert "${param.number}" in section

    def test_it_says_the_name_is_checked_and_which_spelling_to_write(self):
        # Reversed within a day: the sigil was the only spelling that compiled
        # and the name was unchecked; now the sigil is refused (TSF2065) and the
        # format spelling is checked (TSF2021). The entry carries both codes so
        # a reader meeting either knows which side of the change they are on.
        section = self._section()
        assert "TSF2065" in section and "TSF2021" in section
        assert "Re-probe before relying on it" in section

    def test_it_says_what_to_do_when_no_verb_fits(self):
        assert "step addon" in self._section()


class TestTheDynamicParameterCheckIsPerTest:
    """"Check it against the profile" passes a suite that fails on test two.

    An element belongs to a screen, not a profile — shared by every test that
    uses it, with no profile scope of its own — and at run time the value comes
    from whichever profile the executing test is bound to.

    `validate` looks like it helps and only half does. An ordinary value slot is
    checked workspace-wide (TSF2021, verified: a column in no profile is
    refused, a column in *another* profile is accepted). Inside a locator,
    nothing is checked at all.
    """

    def _section(self):
        return " ".join(DOC.section("values, names and layout").split())

    def test_the_manual_check_is_scoped_per_test(self):
        section = self._section()
        assert "per *test*, not per profile" in section
        assert "both" in section

    def test_it_says_why_an_element_has_no_profile_of_its_own(self):
        assert "belongs to a screen, not to a profile" in self._section()

    def test_it_says_the_check_is_workspace_wide(self):
        section = self._section()
        assert "TSF2021" in section
        assert "workspace-wide" in section

    def test_it_says_the_slot_check_is_weaker_than_runtime(self):
        # Pooling is the mechanism and the consequence is the point: a column
        # from any profile satisfies a check the bound profile will have to
        # honour at run time.
        assert "weaker than run time" in self._section()

    def test_it_names_runtime_as_the_only_silent_kind(self):
        # The retracted claim was that a cross-profile `param` passes silently.
        # It throws; only a missing runtime variable is silent.
        section = self._section()
        assert "only one of the three reference kinds is silent" in section.lower()
        assert "fails the run" in section

    def test_it_names_the_script_that_does_the_per_test_pass(self):
        # The "why unbound tests are skipped" half of this assertion went when
        # the skip did — nothing supplies a profile at run time, so those are
        # reported now rather than exempted.
        assert "check_profile_refs.py" in self._section()


class TestTheThreeReferenceKindsBehaveDifferently:
    """Only `runtime` is silent. `param` and `env` fail the run.

    An earlier version of this reference said a cross-profile `param` "passes
    having checked nothing" — a generalisation from runtime-variable behaviour
    that was passed to me as fact and that I built on. `param` throws.
    """

    def _section(self):
        return " ".join(DOC.section("values, names and layout").split())

    def test_it_says_param_fails_the_run(self):
        assert "fails the run" in self._section()

    def test_it_names_runtime_as_the_silent_one(self):
        section = self._section()
        assert "missing **runtime** variable is the silent one" in section

    def test_it_does_not_still_claim_param_passes_silently(self):
        # The retracted sentence, asserted absent so it cannot drift back.
        section = self._section()
        assert "the test passes, having checked nothing" not in section
