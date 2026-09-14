"""The contract every command document must satisfy, plus the resume command.

Structural and topic-presence only, like test_skills.py. Where a test insists on
a word it is because the ticket requires that instruction to exist, never
because of how it reads.
"""

import pytest

from support import (
    document,
    MIGRATION_DIRECTORY,
    PLUGIN_ROOT,
    command_files,
    has_paragraph_with,
    read_frontmatter,
)

RESUME = PLUGIN_ROOT / "commands" / "resume.md"


def _body(path):
    _, body = read_frontmatter(path)
    return body


# --- every command -----------------------------------------------------------

def test_there_is_at_least_one_command():
    assert command_files(), "no commands found; the checks below would prove nothing"


@pytest.mark.parametrize("command", command_files(), ids=lambda p: p.stem)
class TestEveryCommand:
    def test_has_a_description(self, command):
        meta, _ = read_frontmatter(command)
        description = str(meta.get("description", "")).strip()
        assert len(description) > 20, "a command with no description is unfindable"

    def test_body_opens_with_a_title(self, command):
        assert _body(command).lstrip().startswith("# "), "command body has no title"

    def test_a_command_touching_the_migration_directory_points_at_its_definition(self, command):
        body = _body(command)
        touches = MIGRATION_DIRECTORY in body or "migration directory" in body.lower()
        if not touches:
            pytest.skip("this command does not touch the Migration Directory")
        assert "references/migration-directory.md" in body, (
            "the Migration Directory's file set is defined in one place; a document "
            "that reads it must point at that definition rather than restate it"
        )


# --- the resume command ------------------------------------------------------

class TestResumeCommand:
    def test_it_exists(self):
        assert RESUME.is_file()

    def test_its_description_says_it_resumes_a_migration(self):
        meta, _ = read_frontmatter(RESUME)
        description = str(meta.get("description", "")).lower()
        assert "migration" in description
        assert "resume" in description

    def _sections(self):
        # The handle raises on a duplicate heading, which is what stops a
        # gutted section plus a verbatim copy further down from satisfying
        # anything below.
        return document(RESUME).sections

    def _section(self, needle):
        return document(RESUME).section(needle)

    # The four things it must report. Each is scoped to the section that
    # reports it, because these words recur across the whole document.

    # --- Concessions ---------------------------------------------------------
    #
    # A Concession is reviewed work carrying a known difference from the source.
    # Review found resume could not see one: it counts unreviewed rows and reads
    # the two question files, and never looked inside a reviewed row. The model
    # claimed "known and written down" while nothing made it found.

    def test_it_counts_the_concessions(self):
        assert has_paragraph_with(
            self._section("unreviewed"), "count the concessions"
        ), "resume must report concessions, not only unreviewed rows"

    def test_it_says_why_an_unfindable_concession_is_a_divergence(self):
        assert has_paragraph_with(self._section("unreviewed"), "divergence")

    def test_it_reads_the_platform_limits_that_forced_them(self):
        # A limit since lifted turns a Concession back into a row worth redoing.
        assert has_paragraph_with(
            self._section("unreviewed"), "platform-facts.md", "lifted"
        )

    # --- the Conversion queue ------------------------------------------------
    #
    # A Migration runs over days, and the question a fresh session asks is which
    # Conversion is next and whether anything waits on the Operator. A Phase line
    # could not answer it: with survey the only Phase it would read the same for
    # three weeks.

    def test_it_reports_the_conversion_queue(self):
        section = self._section("queue")
        assert has_paragraph_with(section, "scenarios.md", "done", "pending", "parked")

    def test_the_queue_counts_every_status_the_file_defines(self):
        # Four statuses, and a status left uncounted is work nothing reports.
        section = self._section("queue").lower()
        for status in ("pending", "done", "parked", "out-of-scope"):
            assert status in section, f"the queue never counts {status} rows"

    def test_a_parked_scenario_is_reported_with_what_it_waits_on(self):
        # "Two parked" is how a question goes quiet; what each waits on is the
        # one part of this report the Operator alone can act on.
        assert has_paragraph_with(
            self._section("queue"),
            "parked",
            "waits on",
            absent=("a count is enough", "need not say"),
        )

    def test_it_names_which_conversion_would_be_taken_next(self):
        assert has_paragraph_with(self._section("queue"), "next_conversion.py"), (
            "the next Conversion is chosen by the same script convert runs, so "
            "resume and convert cannot name different scenarios"
        )

    def test_naming_the_next_conversion_does_not_take_it(self):
        assert has_paragraph_with(
            self._section("queue"), "do not convert"
        ), "resume reports the queue; converting is convert's work"

    def test_the_phase_framing_is_gone(self):
        # Survey is the only Phase (ADR-0012), so a Phase line would read
        # "converting" for the whole Migration — noise in front of the thing
        # the Operator needs.
        # Scoped rather than a document-wide ban on the word: Phase is live
        # vocabulary (ADR-0012, CONTEXT.md), and survey is one. What is gone is
        # resume reporting one.
        meta, body = read_frontmatter(RESUME)
        assert "phase" not in str(meta.get("description", "")).lower()
        assert "active phase" not in body.lower()
        for heading in (self._section("queue"), self._section("report")):
            assert "phase" not in heading.lower()

    def test_it_names_the_next_thing_to_do(self):
        assert has_paragraph_with(self._section("report"), "next thing to do")

    def test_it_counts_unreviewed_step_map_rows(self):
        section = self._section("unreviewed")
        assert has_paragraph_with(section, "step-map.md", "count")

    def test_unreviewed_rows_are_locatable_not_merely_counted(self):
        # A count with no way to find the rows is a number the Operator cannot act on.
        assert has_paragraph_with(
            self._section("unreviewed"),
            "status",
            "find",
            absent=("no need to find", "without naming", "need not be"),
        )

    def test_it_surfaces_unanswered_questions_every_time(self):
        section = self._section("question")
        assert has_paragraph_with(
            section,
            "open-questions.md",
            "every",
            absent=("only when", "if anything changed"),
        ), "unanswered questions must be surfaced every session, not conditionally"

    def test_it_surfaces_unanswered_application_facts_too(self):
        # An Application Fact nobody answered is an open question that lives in
        # a different file; leaving it out is the same silence by another route.
        # Scoped to the paragraph that says what to read: the filename also
        # appears in a later explanatory paragraph, and section-presence alone
        # passed with the instruction to read it deleted.
        assert has_paragraph_with(
            self._section("question"),
            "open-questions.md",
            "application-facts.md",
            "unanswered",
        ), "both files must be read for unanswered questions, not just one"

    def test_a_question_is_never_reduced_to_a_count(self):
        assert has_paragraph_with(
            self._section("question"),
            "never",
            "count",
            absent=("it is fine to", "acceptable to", "may reduce"),
        ), "a question summarised into a number has gone quiet"

    def test_it_reports_a_changed_cli_build(self):
        # Positive, not co-occurrence: "report it before anything else" survives
        # no hedge. A review demoted this to "you may mention it later if it
        # seems relevant" while keeping every word the old assertion looked for.
        assert has_paragraph_with(
            self._section("cli"), "differs", "before anything else"
        ), "a CLI build that differs from the recorded one must be reported first"

    def test_it_points_at_the_cli_probe_procedure(self):
        assert "references/cli-probe.md" in _body(RESUME), (
            "the probe procedure is defined in one place; do not restate it"
        )

    def test_the_cli_comparison_happens_before_the_report(self):
        # A check whose meaning has changed silently is worse than a missing
        # one, so the Operator learns about it before anything else is said.
        headings = list(self._sections())
        cli = next(i for i, h in enumerate(headings) if "cli" in h.lower())
        report = next(i for i, h in enumerate(headings) if "report" in h.lower())
        assert cli < report

    def test_it_marks_work_checked_under_the_old_build_as_not_checked(self):
        assert has_paragraph_with(self._section("cli"), "not checked", "check-record.md")

    def test_it_handles_a_migration_that_has_only_been_surveyed(self):
        # The commonest second session: survey ran, mapping has not started, and
        # the Step Map holds nothing but its header. Zero unreviewed rows must
        # not read as nothing left to do.
        assert has_paragraph_with(
            self._section("unreviewed"), "no rows", "nothing left to do"
        ) or has_paragraph_with(
            self._section("unreviewed"), "only its header", "nothing left to do"
        )

    def test_it_refuses_when_there_is_no_migration_to_resume(self):
        assert has_paragraph_with(
            self._section("is there a migration"),
            MIGRATION_DIRECTORY,
            "survey",
            "do not create",
        ), "with no Migration Directory there is nothing to resume; say so and name survey"

    def test_it_reports_all_four_things_in_one_report(self):
        # The ticket's headline: one command, four answers, unambiguously.
        section = self._section("report")
        lowered = section.lower()
        for topic in ("queue", "unreviewed", "question", "cli"):
            assert topic in lowered, f"the report never mentions {topic}"

    def test_it_stays_read_only_apart_from_the_correction(self):
        # Reporting must not change what it reports, or two sessions reading the
        # same directory see different states.
        # The preamble's single-write claim is guarded from the other side by
        # test_document_shape. What is new here is that the queue writes nothing
        # either: a parked row that has cleared is returned to `pending` by
        # convert.
        assert has_paragraph_with(
            self._section("queue"), "pending", "convert", "not this one"
        ), "returning a cleared parked row to pending is convert's write"

    def test_a_saturated_queue_is_reported_as_a_default_not_a_recommendation(self):
        # Past saturation the ordering no longer prefers anything, and a default
        # offered as a recommendation takes a choice from the Operator without
        # their knowing it was theirs.
        assert has_paragraph_with(
            self._section("queue"), "saturated", "default", "recommendation"
        )

    def test_no_selection_is_told_apart_from_a_missing_record(self):
        # The script cannot distinguish them by exit status, and a Migration
        # whose records are missing is not a Migration with no work left.
        assert has_paragraph_with(
            self._section("queue"), "missing record", absent=("no work left.",)
        )

    def test_the_scripts_own_output_is_not_relayed_to_the_operator(self):
        # It prints file paths, which the audience rule keeps out of what the
        # Operator sees.
        assert has_paragraph_with(self._section("queue"), "paths", "not relayed") or \
            has_paragraph_with(self._section("queue"), "paths", "nothing here is relayed")

    def test_it_names_the_audience_rule(self):
        assert has_paragraph_with(_body(RESUME), "operator", "context.md")
