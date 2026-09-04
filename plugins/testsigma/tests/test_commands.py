"""The contract every command document must satisfy, plus the resume command.

Structural and topic-presence only, like test_skills.py. Where a test insists on
a word it is because the ticket requires that instruction to exist, never
because of how it reads.
"""

import pytest

from support import (
    MIGRATION_DIRECTORY,
    PLUGIN_ROOT,
    command_files,
    has_paragraph_with,
    markdown_sections,
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
        # Raises on a duplicate heading, which is what stops a gutted section
        # plus a verbatim copy further down from satisfying anything below.
        return markdown_sections(_body(RESUME))

    def _section(self, needle):
        matching = [v for k, v in self._sections().items() if needle in k.lower()]
        assert len(matching) == 1, (
            f"expected exactly one section whose heading contains {needle!r}, found "
            f"{len(matching)}. Headings are: {list(self._sections())}"
        )
        return matching[0]

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

    def test_it_reports_the_active_phase(self):
        assert has_paragraph_with(self._section("phase"), "active phase")

    def test_the_phase_is_decided_by_a_stated_rule_not_by_impression(self):
        # Without a rule written down, two sessions reading the same directory
        # can name different Phases, and the Operator cannot tell which is right.
        section = self._section("phase")
        assert "step-map.md" in section and "migration.md" in section, (
            "the Phase must be read off named files in the Migration Directory"
        )

    def test_the_phase_rule_says_which_row_wins(self):
        section = self._section("phase")
        assert has_paragraph_with(section, "first row"), (
            "several conditions can match at once; the tie-break is the rule"
        )
        # And the rows must be in Phase order, since "first match" is only
        # deterministic against a stated order.
        order = ["extraction", "element resolution", "mapping", "assembly"]
        positions = [section.lower().index(phase) for phase in order]
        assert positions == sorted(positions), (
            f"the Phase rows are out of Phase order: {order}"
        )

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
            self._section("phase"), "no rows", "mapping"
        ) or has_paragraph_with(self._section("phase"), "only its header", "mapping")

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
        for topic in ("phase", "unreviewed", "question", "cli"):
            assert topic in lowered, f"the report never mentions {topic}"

    def test_it_names_the_audience_rule(self):
        assert has_paragraph_with(_body(RESUME), "operator", "context.md")
