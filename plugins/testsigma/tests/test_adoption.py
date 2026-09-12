"""Adopting work a target project already held.

The situation this is for: a team converts part of a suite by hand, then a
Migration starts against the same project. Without a rule the Migration authors
a second copy of everything they wrote, and hands back a project with two of
each and no way to tell which is live.

The failure being designed against is not the duplication itself. It is that a
duplicate is invisible from inside the run: every check passes, the tests are
valid, the tenant takes them, and the damage is only legible to the team who
wrote the originals.
"""

import re

import pytest

from support import (
    REFERENCES_DIR,
    SKILLS_DIR,
    document,
    has_paragraph_with,
    hedges_in,
)

ADOPTION = REFERENCES_DIR / "adoption.md"
DOC = document(ADOPTION)


def _text():
    return DOC.body


def _skill(name):
    return document(SKILLS_DIR / name / "SKILL.md").body


# --- the inventory -----------------------------------------------------------

class TestTheInventoryComesFirst:
    def test_it_names_the_command_that_produces_the_inventory(self):
        # Without the command the rule is an intention. `pull version --write`
        # is the only one that writes a working copy per entity a version holds.
        assert "pull version --write" in _text()

    def test_the_inventory_lands_inside_the_migration_directory(self):
        assert ".testsigma/migration/existing/" in _text()

    def test_survey_pulls_it_rather_than_leaving_it_to_mapping(self):
        # Mapping is where a duplicate would be created, so an inventory pulled
        # at mapping time arrives after the first rows are already decided.
        body = _skill("survey")
        assert "pull version --write" in body
        assert ".testsigma/migration/existing/" in body

    def test_survey_asks_before_pulling(self):
        # Whether anyone converted part of this suite by hand is a fact about
        # the team, not about the project: an empty-looking project may simply
        # be the wrong one.
        assert has_paragraph_with(_skill("survey"), "already converted", "hand")

    def test_an_absent_inventory_is_recorded_rather_than_inferred(self):
        # An empty project and an uninspected one produce an identical absence.
        # Recording which it was is the whole difference between "nothing to
        # adopt" and "nobody looked".
        assert has_paragraph_with(_skill("survey"), "empty", "existing/")

    def test_the_pulled_copies_are_evidence_and_are_not_edited(self):
        # Their entire value is that they say what the project held at the
        # snapshot. An edited copy has stopped saying that, and nothing records
        # that it was edited.
        assert has_paragraph_with(_text(), "evidence", "edited")


# --- read-only ---------------------------------------------------------------

class TestAdoptionIsReadOnly:
    def test_it_forbids_writing_to_the_project_it_adopts_from(self):
        assert has_paragraph_with(_text(), "pull, never push")

    def test_it_names_the_subcommands_a_read_only_project_forbids(self):
        # "Do not push" is read as "do not run `testsigma push`", and the three
        # writing forms that are not spelled `push` slip under it.
        for writer in ("--delete", "--overwrite-remote", "attach"):
            assert writer in _text(), f"a writing path is unnamed: {writer}"

    def test_merging_two_projects_is_the_operators_act_and_not_a_side_effect(self):
        assert has_paragraph_with(_text(), "merge", "Operator")

    def test_survey_records_whether_the_project_may_be_written_to(self):
        # Every later stage decides where to push from this. Unrecorded, a
        # read-only project is discovered by writing to it.
        assert has_paragraph_with(_skill("survey"), "read-only", "application-facts.md")


# --- the status --------------------------------------------------------------

class TestTheAdoptedStatus:
    DIRECTORY = document(REFERENCES_DIR / "migration-directory.md").body

    def test_the_status_vocabulary_names_adopted(self):
        assert re.search(
            r"status is one of.*`adopted`", self.DIRECTORY
        ), "the fixed vocabulary does not admit the status the rule requires"

    def test_adopted_is_not_a_kind_of_reviewed(self):
        # They answer different questions — one says a person decided how to
        # express this step, the other that a person decided it was already
        # expressed — and a report merging them answers neither what is left nor
        # what this Migration produced.
        assert has_paragraph_with(self.DIRECTORY, "adopted", "not a kind of `reviewed`")

    def test_an_adopted_row_names_its_entity_behind_a_fixed_prefix(self):
        # Same reason `Concession:` and `Kind:` are fixed: the reviewer's
        # question is "show me everything this Migration did not write", and a
        # fixed prefix makes that a sweep rather than a reading.
        assert "Adopted:" in _text()
        assert "Adopted:" in self.DIRECTORY

    def test_existing_is_not_one_of_the_seven_files(self):
        assert has_paragraph_with(self.DIRECTORY, "existing/", "seven")


# --- assembly ----------------------------------------------------------------

class TestAnAdoptedRowIsStillAssembled:
    def test_assemble_builds_from_adopted_rows(self):
        assert has_paragraph_with(_skill("assemble"), "`reviewed` or `adopted`")

    def test_it_says_the_scenario_still_gets_a_step(self):
        # The natural misreading is "someone else wrote it, so skip it", which
        # leaves the scenario silently short of that step — the same hole an
        # empty marker block exists to prevent.
        assert has_paragraph_with(_skill("assemble"), "adopted", "coverage counts it")


# --- verification ------------------------------------------------------------

class TestVerifyBeforeAdopting:
    def test_it_runs_the_same_check_that_guards_an_authored_row(self):
        # An adopted row and an authored one are read identically by everything
        # after mapping, so both must have cleared the same bar to get there.
        assert "check_call_chain.py" in _text()

    def test_it_verifies_against_the_pulled_copy_and_names_the_symbol(self):
        assert "--symbol" in _text() and "existing/" in _text()

    def test_could_not_compare_is_not_a_pass(self):
        # Exit 2 is the check's own report that it is blind here. Recorded as a
        # pass it becomes a claim the next session has no way to doubt.
        assert has_paragraph_with(_text(), "exit 2")

    def test_a_disagreement_goes_to_the_operator_rather_than_being_repaired(self):
        # The existing entity is live: something runs it, and a team believes it
        # covers this step. A run that "fixes" it has overwritten their
        # judgement with its own, silently.
        assert has_paragraph_with(_text(), "disagrees", "Operator")

    def test_adoption_is_never_bulk(self):
        assert has_paragraph_with(_text(), "bulk")

    def test_checks_carries_the_adoption_case_under_the_source_comparison(self):
        # Discoverability: a reader looking for what verifies an adoption looks
        # in checks.md, not in a reference they have not been told about.
        assert "adoption.md" in document(REFERENCES_DIR / "checks.md").body


# --- matching ----------------------------------------------------------------

class TestMatching:
    def test_it_matches_on_behaviour_rather_than_on_name(self):
        # A name is how a team found an entity again. Two teams converting the
        # same step name it two different things, and the same name over
        # different actions is the dangerous pairing.
        assert has_paragraph_with(_text(), "not on what it is called")

    def test_adoption_is_optional_and_not_a_stage(self):
        assert has_paragraph_with(_text(), "never a stage")


def test_the_reference_states_rules_rather_than_granting_permission():
    # A rule is most often gutted by adding a paragraph that grants permission,
    # not by editing the rule.
    assert not hedges_in(_text())
