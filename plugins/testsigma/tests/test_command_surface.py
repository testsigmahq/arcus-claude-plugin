"""Every command the plugin names has an owner, or a stated absence.

Two opposite faults, and one audit could find neither. `run` sits in the
seven-command table as part of "the workspace CLI this plugin needs" and appears
nowhere else: no stage drives it and nothing says why, so a reader takes it for a
command whose instructions they have not found yet. `attach` is the reverse —
described in four files, each correctly, owned by none, so every individual
reading looks complete.

The rule both are held to: a command or flag earns a line where a flow is wrong
or weaker without it, and the line lives in that flow's document. The tool's help
owns the rest, because a table of the whole surface is a second copy of `--help`
that goes stale the way ADR-0009's block count did.
"""

import pytest

from support import (
    REFERENCES_DIR,
    SKILLS_DIR,
    document,
    has_paragraph_with,
)

PROBE = document(REFERENCES_DIR / "cli-probe.md").body
AUTHORING = document(REFERENCES_DIR / "authoring.md").body
DIRECTORY = document(REFERENCES_DIR / "migration-directory.md").body
ADOPTION = document(REFERENCES_DIR / "adoption.md").body
DELIVERY = document(REFERENCES_DIR / "delivery.md").body
MAP = document(SKILLS_DIR / "map" / "SKILL.md").body


# --- run ---------------------------------------------------------------------

class TestRunIsOutOfScopeAndSaysSo:
    def test_the_table_says_a_migration_does_not_run_tests(self):
        # Listing it under "the CLI this plugin needs" while no stage drives it
        # reads as an instruction the reader has not located yet.
        assert has_paragraph_with(PROBE, "never executes")

    def test_it_gives_the_reason_rather_than_only_the_exclusion(self):
        # "run" is a substring of "running" and "run a Migration", both of which
        # this file is full of, so the words alone assert nothing.
        assert has_paragraph_with(PROBE, "needs a tenant, agents and test data")

    def test_the_table_row_stops_promising_a_command_no_stage_drives(self):
        assert "The workspace CLI this plugin needs" not in PROBE


# --- attach ------------------------------------------------------------------

class TestAttachHasOneOwner:
    def test_the_owner_describes_what_attach_establishes(self):
        # A heading alone satisfied the earlier form of this.
        assert has_paragraph_with(AUTHORING, "The folder it attaches is the Target Project")
        assert has_paragraph_with(AUTHORING, "writes `applicationType` into the marker")

    def test_the_owner_names_its_positional_arguments(self):
        assert has_paragraph_with(AUTHORING, "project, application, version")

    def test_the_probe_points_at_the_owner_rather_than_restating_it(self):
        # `cli-probe.md` already named authoring.md before this rule existed, so
        # the bare filename passes on the text this was written against.
        assert has_paragraph_with(PROBE, "describes what it establishes")

    def test_delivery_points_at_the_owner_too(self):
        # A raw `in` misses this: the pointer spans a line wrap, which the
        # helper normalises and a substring check does not.
        assert has_paragraph_with(DELIVERY, "What `attach` establishes")


# --- generators --------------------------------------------------------------

class TestTheGeneratorVerdictCanBeChecked:
    def test_the_listing_form_is_named_where_the_verdict_is_reached(self):
        # `map` tells a reader to record "no generator produces this value" and
        # nothing said how to establish it. Bare `list generators` is an index
        # of counts per group, so naming the command without the form sends a
        # reader to output that answers nothing.
        assert "list generators --all" in DIRECTORY

    def test_the_index_is_distinguished_from_the_listing(self):
        assert has_paragraph_with(DIRECTORY, "index of counts", "wrong thing")

    def test_generators_are_stated_to_be_one_catalogue(self):
        # "not one catalogue" also matches the two words. And a reader who has
        # just learned the verb dialect rule will assume it carries over.
        assert has_paragraph_with(AUTHORING, "one catalogue, not two")
        assert has_paragraph_with(AUTHORING, "--dialect", "changes nothing")

    def test_the_verdict_is_two_questions_and_names_the_second_refusal(self):
        # An `or` over two homes cannot enforce one owner — it licenses exactly
        # the fault this module was written against. `authoring.md` owns the
        # rule; migration-directory.md points at it.
        assert has_paragraph_with(AUTHORING, "TSF2012", "not the generator being absent")
        assert "authoring.md" in DIRECTORY


# --- deprecation -------------------------------------------------------------

class TestMappingCanReachTheDeprecationRule:
    def test_map_points_at_the_rule_rather_than_holding_a_copy(self):
        # The stage that picks verbs never mentioned deprecation at all. It gets
        # a pointer and not a copy: `map` sits a handful of words inside its
        # progressive-disclosure budget, and the detail belongs in a reference.
        assert has_paragraph_with(MAP, "which verbs are deprecated", "authoring.md")

    def test_the_rule_records_that_the_default_listing_hides_them(self):
        # This is what makes enumerate-first protective rather than merely
        # tidy: a verb you cannot see is a verb you cannot pick.
        assert has_paragraph_with(AUTHORING, "hidden by default")

    def test_the_flag_is_described_as_including_rather_than_filtering(self):
        # "shows only the deprecated ones" leads to the opposite instruction.
        assert has_paragraph_with(AUTHORING, "includes the rest rather than filtering")

    def test_the_warning_and_the_refusal_are_separated(self):
        # `validate` warns and exits 0; `push` refuses a new step outright. A
        # session reading the exit code carries the row to the refusal.
        assert has_paragraph_with(AUTHORING, "TSF2008", "warning")
        assert has_paragraph_with(AUTHORING, "TSS1106", "refuses")

    def test_the_refusal_is_scoped_to_a_new_step(self):
        # An entity that already has a step on that template keeps it. Dropping
        # the qualifier turns a narrow gate into a blanket ban.
        assert has_paragraph_with(AUTHORING, "only for a *new* step")


# --- prune -------------------------------------------------------------------

class TestThePruneHazardIsTheRealOne:
    def test_the_hazard_named_is_the_soft_deleted_one(self):
        # The word alone appears in any paragraph discussing it at all.
        assert has_paragraph_with(ADOPTION, "cannot tell them apart")

    def test_the_document_says_prune_cannot_reach_the_evidence_directory(self):
        # It walks `tests/testsigma` only, settled kinds only, bound files only.
        # A negative guard cannot express this: the correct prose says "never
        # anything under `existing/`", which contains every term such a guard
        # would ban. So the disclaimer itself is what gets asserted.
        assert has_paragraph_with(ADOPTION, "--prune", "outside the workspace root")

    def test_the_hazard_is_not_overstated_as_evidence_destruction(self):
        # A reader told a false hazard stops believing the true ones.
        assert has_paragraph_with(ADOPTION, "never anything under")

    def test_the_dry_run_that_precedes_it_is_named(self):
        assert has_paragraph_with(ADOPTION, "--prune", "without `--write`")
