"""Sending a Migration's committed working copy to the Target Project.

The situation this is for: the plugin mentioned `push` exactly once, in
`adoption.md`, as a prohibition scoped to a read-only source project. Every
skill ended at "commit the working copy". So a reader who worked through the
whole plugin concluded a Migration never delivers to a tenant, and was wrong.

The failure being designed against is that shape of absence. A correctly-scoped
rule whose counterpart is undocumented does not read as narrow — it reads as
general, and there is nothing beside it to say otherwise. Writing the second
world is what makes the first one safe to read.
"""

from support import (
    REFERENCES_DIR,
    document,
    has_paragraph_with,
    hedges_in,
)

DELIVERY = REFERENCES_DIR / "delivery.md"
DOC = document(DELIVERY)


def _text():
    return DOC.body


# --- the target --------------------------------------------------------------

class TestWhatIsDeliveredInto:
    def test_the_target_is_the_attached_folder(self):
        # A Migration that asked again could be told a different answer than the
        # one its files are already bound to.
        assert has_paragraph_with(_text(), "the folder the new tests are written in")

    def test_it_says_the_target_is_not_pinned_a_second_time(self):
        assert has_paragraph_with(_text(), "never asks which project")


# --- who triggers it ---------------------------------------------------------

class TestNoConversionPushes:
    def test_it_says_plainly_that_a_conversion_does_not_push(self):
        # "A Conversion pushes" satisfies any co-occurrence of the two words,
        # so the negation itself has to be the thing asserted.
        assert has_paragraph_with(_text(), "does not send anything")

    def test_the_operator_picks_the_moment(self):
        assert has_paragraph_with(_text(), "operator", "moment")

    def test_it_gives_the_reason_rather_than_the_rule_alone(self):
        # The reason is the blast radius: an upload version reaches beyond the
        # target version, so the moment has to be attributable to a person.
        assert has_paragraph_with(_text(), "upload", "version", "attributable")


# --- the two worlds ----------------------------------------------------------

class TestTheTwoWorldsAreScoped:
    def test_delivery_names_the_common_case_as_one_project(self):
        assert has_paragraph_with(_text(), "one", "target", "project")

    def test_it_names_the_read_only_source_project_as_the_other_world(self):
        assert has_paragraph_with(_text(), "read-only", "source project")


# --- the foreign-id trap -----------------------------------------------------

class TestTheForeignIdTrap:
    def test_it_describes_ids_as_per_tenant(self):
        assert has_paragraph_with(_text(), "id", "tenant")

    def test_the_baseline_is_named_as_what_catches_it(self):
        assert has_paragraph_with(_text(), "baseline", "TSS1201")

    def test_an_absent_id_refuses_with_its_own_code(self):
        assert "TSS1101" in _text()

    def test_validate_is_stated_to_be_offline_and_unable_to_see_it(self):
        assert has_paragraph_with(_text(), "validate", "offline")

    def test_the_name_comparison_is_described_as_a_notice_that_renames(self):
        # This is the comparison that looks like protection and is not. A name
        # mismatch is exit 0, and for a test it renames the target entity.
        assert has_paragraph_with(_text(), "TSS1109", "notice")
        assert has_paragraph_with(_text(), "TSS1109", "rename")

    def test_the_name_is_never_offered_as_the_guard(self):
        # `absent=("not",)` cannot express this: "not" is inside *notice*,
        # *nothing* and *note*, which this document is full of. So assert the
        # positive claim the document has to make instead.
        assert has_paragraph_with(_text(), "looks like protection and is not")


# --- bindings ----------------------------------------------------------------

class TestHowAnIdEntersAFile:
    def test_hand_writing_a_binding_is_forbidden(self):
        assert has_paragraph_with(_text(), "never by hand")

    def test_it_says_why_a_hand_written_binding_is_worse_than_wrong(self):
        # TSS1111 is a notice, so nothing refuses: binding proceeds on the id
        # alone with nothing compared.
        assert "TSS1111" in _text()

    def test_adopt_id_is_named_as_the_sanctioned_route(self):
        assert "--adopt-id" in _text()

    def test_adopt_id_is_not_described_as_writing_a_baseline(self):
        # It writes the binding and nothing else. Describing it as a complete
        # substitute would promise a guard that is not there — and asserting
        # only that the two words co-occur would pass on prose promising it.
        assert has_paragraph_with(_text(), "--adopt-id", "no hash")
        assert has_paragraph_with(_text(), "--adopt-id", "also carries no baseline")

    def test_adopt_id_is_stated_to_be_safe_from_the_wrong_tenant(self):
        assert has_paragraph_with(_text(), "cannot", "bind a foreign id")


# --- the flags ---------------------------------------------------------------

class TestTheFlags:
    def test_dry_run_precedes_every_push(self):
        assert has_paragraph_with(_text(), "--dry-run", "every push")

    def test_dry_run_is_not_described_as_doubt_triggered(self):
        # "Run it where there is reason to doubt the bindings" contains the word
        # doubt and is the exact rule this forbids, so the word cannot be the
        # assertion. The refusal of that framing is.
        assert has_paragraph_with(_text(), "not where there is reason to doubt")

    def test_dry_run_is_not_promised_as_a_perfect_rehearsal(self):
        assert "TSS1138" in _text()

    def test_a_migration_never_passes_overwrite_remote(self):
        assert has_paragraph_with(_text(), "--overwrite-remote", "is never passed")

    def test_discard_healing_is_never_routine(self):
        assert has_paragraph_with(_text(), "--discard-healing", "never routine")

    def test_delete_is_described_as_reaching_the_local_file_too(self):
        assert has_paragraph_with(_text(), "--delete", "local file")

    def test_delete_says_when_a_migration_may_use_it(self):
        # Every other flag says when. This one said only what it does, which
        # reads as an ordinary tool rather than one a Migration never reaches for.
        assert has_paragraph_with(_text(), "--delete", "is never passed")

    def test_removing_a_version_block_is_not_a_delete(self):
        assert has_paragraph_with(_text(), "version block", "deletes nothing")


# --- uploads -----------------------------------------------------------------

class TestTheUploadThatEscapesTheTarget:
    """The one write a Migration cannot confine to the Target Project.

    Everything else Delivery sends lands in the version the working copy is
    attached to. A new version of an existing upload does not: the server
    repoints every referencing step at it, across the application's other
    versions, where nobody is watching and nothing connects the change back.
    """

    def test_a_new_upload_is_free(self):
        # "A new upload is not free even though nothing references it yet"
        # satisfies a co-occurrence of the two halves, so assert the claim.
        assert has_paragraph_with(_text(), "a new upload is free")

    def test_a_new_version_of_an_existing_upload_is_not(self):
        assert has_paragraph_with(_text(), "reaches past the Target Project")

    def test_an_id_less_upload_line_is_always_a_new_upload(self):
        # "always" and "new upload" both appear in the heading above this rule,
        # and in "not always a new upload". The absence of matching is the fact.
        assert has_paragraph_with(_text(), "is a create, every time")
        assert has_paragraph_with(_text(), "no filename matching")

    def test_pulling_the_target_uploads_is_named_as_how_to_avoid_a_twin(self):
        # The command alone is satisfied by "do not run `pull uploads --write`".
        # What it is for has to be in the same paragraph as the command.
        assert has_paragraph_with(_text(), "pull uploads --write", "twin")

    def test_consent_is_per_upload_rather_than_per_delivery(self):
        assert has_paragraph_with(_text(), "consent is per upload")

    def test_agreeing_to_the_delivery_is_stated_not_to_be_that_consent(self):
        # Otherwise one trigger for the whole Delivery reads as sufficient.
        assert has_paragraph_with(_text(), "is not that consent")


class TestTheBlastRadiusIsNotEnumerable:
    def test_it_says_the_repointed_steps_cannot_be_listed(self):
        assert has_paragraph_with(_text(), "cannot be listed")

    def test_it_says_the_plugin_asks_anyway(self):
        # An unanswerable question asked honestly beats a blast radius reported
        # as empty because nobody could look.
        assert has_paragraph_with(_text(), "names none of them")

    def test_the_workspace_is_not_offered_as_the_blast_radius(self):
        # The tests on disk are the ones NOT at risk, so listing them would read
        # as a survey containing none of the thing surveyed. An existence check
        # on "not at risk" would still pass with such a list added beside it.
        assert has_paragraph_with(
            _text(), "a survey of the blast radius while containing none of it"
        )


class TestTheUploadRefusals:
    def test_a_bound_block_carrying_a_path_is_named(self):
        assert has_paragraph_with(_text(), "TSS1157", "cannot be replaced")

    def test_the_remaining_upload_refusals_are_named_with_their_meaning(self):
        # A code with no meaning beside it is a string to search for, not
        # something an Operator can act on.
        assert has_paragraph_with(_text(), "TSS1156", "empty version")
        assert has_paragraph_with(_text(), "TSS1117", "resolves to neither")

    def test_uploads_cannot_be_forced_past_a_baseline_mismatch(self):
        # "a flag appends past TSS1201" keeps both terms. That none is offered
        # is the rule.
        assert has_paragraph_with(_text(), "TSS1201", "none is offered")

    def test_the_two_refusals_described_elsewhere_are_cross_referenced(self):
        # An Operator meeting one of these under an upload push has nothing to
        # look up if the upload section lists only the four the plan raises.
        assert has_paragraph_with(_text(), "TSS1101", "names no upload")
        assert has_paragraph_with(_text(), "TSS1138", "once for real")

    def test_an_unchanged_push_is_described_by_what_it_says_not_by_its_code(self):
        # The code that carries this is overloaded: one number covers four
        # different notices, including "used by N other tests", which never
        # fires for an upload. The sentence identifies the outcome; the code
        # does not, so quoting the number would mislead whoever looked it up.
        assert has_paragraph_with(_text(), "already holds", "nothing to send")

    def test_the_overloaded_notice_code_is_never_cited(self):
        # A regression guard rather than a description: the code is absent today
        # because citing it was decided against, and the number looks
        # authoritative enough that a later editor would add it back in good
        # faith. This fails the moment they do.
        assert "TSS1110" not in _text()


# --- the rules stay rules ----------------------------------------------------

class TestNothingGrantsItselfAnException:
    def test_the_document_hedges_nowhere(self):
        assert hedges_in(_text()) == []
