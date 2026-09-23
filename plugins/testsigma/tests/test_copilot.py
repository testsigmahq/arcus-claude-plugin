"""The Copilot Run, held to ADR-0016.

Two halves. The script is run rather than read, for the reason
`test_next_conversion.py` gives: a check whose own tests only read the document
describing it passes while the mechanism is broken. The documents are held to
the rules a later edit would most cheaply drop — presence and bindingness, never
wording.
"""

import subprocess
import sys
import textwrap

from support import (
    CONTEXT,
    PLUGIN_ROOT,
    REFERENCES_DIR,
    SKILLS_DIR,
    document,
    has_paragraph_with,
)

SCRIPT = PLUGIN_ROOT / "scripts" / "copilot_status.py"
SKILL = document(SKILLS_DIR / "copilot" / "SKILL.md").body
DIRECTORY = document(REFERENCES_DIR / "migration-directory.md").body
PROBE = document(REFERENCES_DIR / "cli-probe.md").body
DELIVERY = document(REFERENCES_DIR / "delivery.md").body
RESUME = document(PLUGIN_ROOT / "commands" / "resume.md").body
CONVERT = document(SKILLS_DIR / "convert" / "SKILL.md").body

SCENARIOS = """\
# Scenarios

| Scenario | Source Steps reached | Status | Reason |
|---|---|---|---|
| `Archive a record` | `I am signed in` | done | |
| `Print a label` | `I am signed in` | done | |
| `Search` | `I am signed in` | pending | |
"""

ASSEMBLED = """\
# Assembled

| Scenario | Test | Row versions consumed | Assembled |
|---|---|---|---|
| `Archive a record` | `archive-a-record.sigma` | `I am signed in`@1 | 2026-09-10 |
| `Print a label` | `print-a-label.sigma` | `I am signed in`@1 | 2026-09-12 |
"""

RUNS_HEADER = """\
# Runs: {name}

| Run | Started | Verdict | Steps skipped | Edits | Notes |
|---|---|---|---|---|---|
"""


def suite(tmp_path, runs=None, scenarios=SCENARIOS, assembled=ASSEMBLED):
    migration = tmp_path / ".testsigma" / "migration"
    migration.mkdir(parents=True)
    (migration / "scenarios.md").write_text(scenarios, encoding="utf-8")
    (migration / "assembled.md").write_text(assembled, encoding="utf-8")
    for test, rows in (runs or {}).items():
        (migration / "runs").mkdir(exist_ok=True)
        body = RUNS_HEADER.format(name=test) + "".join(r + "\n" for r in rows)
        (migration / "runs" / f"{test}.md").write_text(body, encoding="utf-8")
    return tmp_path


def run(path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--suite", str(path)],
        capture_output=True, text=True,
    )


# --- the script --------------------------------------------------------------

class TestCopilotStatus:
    def test_nothing_run_names_the_oldest_delivered_test(self, tmp_path):
        result = run(suite(tmp_path))
        assert result.returncode == 1
        assert "0 of 2" in result.stdout
        assert "Next to run: Archive a record" in result.stdout

    def test_a_pending_scenario_is_not_delivered(self, tmp_path):
        # `Search` has no assembled row and is not done; counting it would put
        # an undelivered test in the denominator.
        assert "of 2 " in run(suite(tmp_path)).stdout

    def test_a_pass_after_assembly_proves_the_test(self, tmp_path):
        result = run(suite(tmp_path, runs={
            "archive-a-record": ["| 1031 | 2026-09-11 | passed | | 0 | |"],
        }))
        assert "1 of 2" in result.stdout
        assert "Next to run: Print a label" in result.stdout

    def test_a_pass_before_the_latest_assembly_is_stale(self, tmp_path):
        # A re-opened scenario is assembled again. A pass recorded before that
        # proved a test that no longer exists.
        result = run(suite(tmp_path, runs={
            "archive-a-record": ["| 1031 | 2026-09-09 | passed | | 0 | |"],
        }))
        assert "0 of 2" in result.stdout
        assert "stale" in result.stdout

    def test_the_latest_run_decides_not_any_run(self, tmp_path):
        result = run(suite(tmp_path, runs={
            "archive-a-record": [
                "| 1031 | 2026-09-11 | passed | | 0 | |",
                "| 1040 | 2026-09-13 | failed | | 1 | |",
            ],
        }))
        assert "0 of 2" in result.stdout
        assert "failed" in result.stdout

    def test_stopped_is_not_proved(self, tmp_path):
        result = run(suite(tmp_path, runs={
            "archive-a-record": ["| 1031 | 2026-09-11 | stopped | 4 | 0 | |"],
        }))
        assert "0 of 2" in result.stdout

    def test_every_test_proved_exits_zero(self, tmp_path):
        result = run(suite(tmp_path, runs={
            "archive-a-record": ["| 1031 | 2026-09-11 | passed | | 0 | |"],
            "print-a-label": ["| 1032 | 2026-09-12 14:02 | passed | | 2 | |"],
        }))
        assert result.returncode == 0, result.stdout
        assert "2 of 2" in result.stdout

    def test_a_missing_record_is_not_a_pass(self, tmp_path):
        migration = tmp_path / ".testsigma" / "migration"
        migration.mkdir(parents=True)
        (migration / "scenarios.md").write_text(SCENARIOS, encoding="utf-8")
        result = run(tmp_path)
        assert result.returncode == 1
        assert "assembled.md" in result.stdout


# --- the documents -----------------------------------------------------------

class TestTheSkill:
    def test_it_runs_one_test_and_stops(self):
        assert has_paragraph_with(SKILL, "exactly one test", "do not take the next")

    def test_every_edit_is_put_to_the_operator_before_it_is_pushed(self):
        assert has_paragraph_with(SKILL, "every edit to the operator", "before it is written")

    def test_the_drift_row_is_written_before_the_push(self):
        assert has_paragraph_with(SKILL, "drift row first", "before the push")

    def test_it_forbids_weakening_a_check_to_pass(self):
        assert has_paragraph_with(SKILL, "never weaken", "divergence")

    def test_a_row_defect_gets_maps_reading_of_the_helper(self):
        assert has_paragraph_with(SKILL, "row is wrong", "open the helper",
                                  "fault-classes.md#conducting-the-comparison")

    def test_a_row_defect_re_opens_the_tests_built_on_it(self):
        assert "invalidated_scenarios.py" in SKILL
        assert "check_row_versions.py" in SKILL

    def test_recorded_drift_is_put_back_after_re_assembly(self):
        assert has_paragraph_with(SKILL, "drift/<test>.md", "re-apply")

    def test_the_verdict_is_read_before_another_run_deletes_it(self):
        assert has_paragraph_with(SKILL, "result --json", "deletes")

    def test_the_run_is_stopped_before_its_verdict_is_read(self):
        # Live on the Go executor: a debug run holds at its end until `stop`,
        # and `result` before that has no verdict. The CLI help once said the
        # opposite, and a skill that waited for the run to end would wait
        # forever.
        assert has_paragraph_with(SKILL, "never ends by itself", "atend", "stop")

    def test_the_verdict_is_read_from_the_field_not_the_exit_code(self):
        assert has_paragraph_with(SKILL, "`verdict` field", "exit 3")

    def test_the_first_push_needs_its_own_yes(self):
        assert has_paragraph_with(SKILL, "wait for a yes", "first push")

    def test_it_runs_only_on_this_machines_agent(self):
        assert has_paragraph_with(SKILL, "agents list", "this machine")

    def test_passed_is_not_equivalence(self):
        assert has_paragraph_with(SKILL, "passed means the test runs")


class TestTheRecords:
    def test_both_are_per_test_and_created_by_copilot(self):
        assert has_paragraph_with(DIRECTORY, "`runs/`", "`drift/`", "not among the nine")

    def test_the_two_rulings_are_the_complete_set(self):
        assert has_paragraph_with(DIRECTORY, "`test-local`", "row stays")
        assert has_paragraph_with(DIRECTORY, "`row defect`", "`version` bumped")

    def test_test_local_drift_does_not_move_the_version(self):
        assert has_paragraph_with(DIRECTORY, "drift", "`version` does not move")

    def test_proved_needs_a_run_since_the_last_assembly(self):
        assert has_paragraph_with(DIRECTORY, "proved", "`assembled` date")

    def test_a_weakening_edit_is_a_sweepable_column(self):
        assert "| Changes what is checked |" in DIRECTORY

    def test_the_glossary_names_both_terms(self):
        body = CONTEXT.read_text(encoding="utf-8")
        assert "**Copilot Run**:" in body
        assert "**Drift**:" in body


class TestTheExceptionIsStatedWhereTheRuleIs:
    def test_the_probe_names_the_one_exception(self):
        # "never executes" still holds of every Conversion; a reader of the
        # probe alone must not conclude a Migration never runs a test.
        assert has_paragraph_with(PROBE, "one exception", "test debug", "adr-0016")

    def test_delivery_says_a_copilot_run_is_a_delivery(self):
        assert has_paragraph_with(DELIVERY, "copilot", "delivery of one test", "adr-0014")

    def test_resume_reports_proved_of_delivered(self):
        assert "copilot_status.py" in RESUME
        assert has_paragraph_with(RESUME, "proved of tests delivered")

    def test_convert_hands_over_to_copilot(self):
        assert has_paragraph_with(CONVERT, "copilot", "own invocation")
