"""The queue's own consistency.

`scenarios.md` answers two questions at once — what is left, and what it would
cost — and every later number is read off it. A `done` scenario with no
assembled test inflates the number the customer is given; a `parked` one with no
reason is a wait nobody can end; a row holding two statuses is counted twice or
not at all, depending on who reads it.

Prior art for the shape of these: `test_committed_check.py` and
`test_coverage_check.py` — run the script, never assert prose about it.
"""

import subprocess
import sys
import textwrap

import pytest

from support import PLUGIN_ROOT

SCRIPT = PLUGIN_ROOT / "scripts" / "check_scenarios.py"

ASSEMBLED = """\
# Assembled

| Scenario | Test | Row versions consumed | Assembled |
|---|---|---|---|
| `Sign in` | `sign-in.sigma` | `I am signed in`@1 | 2026-09-01 |
"""

GOOD = """\
# Scenarios

| Scenario | Source Steps reached | Status | Reason |
|---|---|---|---|
| `Sign in` | `I am signed in` | done | |
| `Search` | `I search` | pending | |
| `Archive` | `I archive` | parked | Waiting on which Submit is live |
| `Print` | `I print` | out-of-scope | Drives a desktop application |
"""


def write(tmp_path, scenarios=GOOD, assembled=ASSEMBLED):
    migration = tmp_path / ".testsigma" / "migration"
    migration.mkdir(parents=True, exist_ok=True)
    (migration / "scenarios.md").write_text(textwrap.dedent(scenarios), encoding="utf-8")
    if assembled is not None:
        (migration / "assembled.md").write_text(textwrap.dedent(assembled), encoding="utf-8")
    return migration


def run(tmp_path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--suite", str(tmp_path)],
        capture_output=True, text=True,
    )


def test_a_consistent_queue_passes(tmp_path):
    write(tmp_path)
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout


class TestEachFailure:
    def test_done_with_no_assembled_row_is_rejected(self, tmp_path):
        # The delivered count is read off `done`, so this is the number the
        # customer is given being wrong.
        write(tmp_path, scenarios=GOOD.replace(
            "| `Search` | `I search` | pending | |",
            "| `Search` | `I search` | done | |"))
        result = run(tmp_path)
        assert result.returncode == 1
        assert "Search" in result.stdout

    def test_parked_with_no_reason_is_rejected(self, tmp_path):
        write(tmp_path, scenarios=GOOD.replace(
            "| `Archive` | `I archive` | parked | Waiting on which Submit is live |",
            "| `Archive` | `I archive` | parked | |"))
        result = run(tmp_path)
        assert result.returncode == 1
        assert "Archive" in result.stdout

    def test_out_of_scope_with_no_reason_is_rejected(self, tmp_path):
        # An out-of-scope row exists to tell "somebody looked and ruled it out"
        # from "nobody looked", and with no reason it cannot.
        write(tmp_path, scenarios=GOOD.replace(
            "| `Print` | `I print` | out-of-scope | Drives a desktop application |",
            "| `Print` | `I print` | out-of-scope | |"))
        result = run(tmp_path)
        assert result.returncode == 1
        assert "Print" in result.stdout

    def test_two_statuses_in_one_cell_are_rejected(self, tmp_path):
        write(tmp_path, scenarios=GOOD.replace(
            "| `Search` | `I search` | pending | |",
            "| `Search` | `I search` | pending, parked | |"))
        result = run(tmp_path)
        assert result.returncode == 1
        assert "Search" in result.stdout

    def test_one_scenario_listed_twice_with_different_statuses_is_rejected(self, tmp_path):
        # The commonest way two statuses arrive: an appended row rather than an
        # edited one. Whichever a reader takes, the other is a lie.
        write(tmp_path, scenarios=GOOD + "| `Search` | `I search` | done | |\n")
        result = run(tmp_path)
        assert result.returncode == 1
        assert "Search" in result.stdout

    def test_a_status_outside_the_four_is_rejected(self, tmp_path):
        # The four are the complete set; resume counts the rows in each state
        # and a private fifth value is counted as none of them.
        write(tmp_path, scenarios=GOOD.replace(
            "| `Search` | `I search` | pending | |",
            "| `Search` | `I search` | in-progress | |"))
        result = run(tmp_path)
        assert result.returncode == 1
        assert "in-progress" in result.stdout

    def test_one_scenario_listed_twice_with_the_same_status_is_rejected(self, tmp_path):
        # Quieter than two disagreeing rows and just as wrong: every total is a
        # count of rows, so the delivered number and the denominator are each
        # out by one.
        write(tmp_path, scenarios=GOOD + "| `Search` | `I search` | pending | |\n")
        result = run(tmp_path)
        assert result.returncode == 1
        assert "Search" in result.stdout

    def test_a_row_with_no_status_at_all_is_rejected(self, tmp_path):
        write(tmp_path, scenarios=GOOD.replace(
            "| `Search` | `I search` | pending | |",
            "| `Search` | `I search` |  | |"))
        result = run(tmp_path)
        assert result.returncode == 1
        assert "Search" in result.stdout


class TestWhatItReports:
    def test_it_reports_every_failure_rather_than_the_first(self, tmp_path):
        # Fixing a queue one rejection per run is how a check stops being run.
        write(tmp_path, scenarios=GOOD.replace(
            "| `Search` | `I search` | pending | |",
            "| `Search` | `I search` | done | |").replace(
            "| `Archive` | `I archive` | parked | Waiting on which Submit is live |",
            "| `Archive` | `I archive` | parked | |"))
        out = run(tmp_path).stdout
        assert "Search" in out and "Archive" in out

    def test_it_carries_none_of_the_forbidden_detail(self, tmp_path):
        write(tmp_path, scenarios=GOOD.replace(
            "| `Search` | `I search` | pending | |",
            "| `Search` | `I search` | done | |"))
        out = run(tmp_path).stdout
        for forbidden in (".testsigma/migration", "Traceback", ".py"):
            assert forbidden not in out


class TestWhenTheFilesAreNotThere:
    def test_a_missing_queue_is_reported_rather_than_read_as_consistent(self, tmp_path):
        (tmp_path / ".testsigma" / "migration").mkdir(parents=True)
        result = run(tmp_path)
        assert result.returncode == 1
        assert "scenarios.md" in result.stdout

    def test_a_missing_assembled_file_is_reported(self, tmp_path):
        write(tmp_path, assembled=None)
        result = run(tmp_path)
        assert result.returncode == 1
        assert "assembled.md" in result.stdout
