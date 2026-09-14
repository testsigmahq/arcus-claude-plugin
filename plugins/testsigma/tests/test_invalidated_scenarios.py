"""Finding the tests a corrected row superseded.

The obligation is old: `migration-directory.md` already says a row that fails
re-check "stops being `reviewed` and is worked again, along with every test
already assembled from it". Under whole-suite Phases no test existed when a row
was revised, so nothing had to find them. Conversions make it reachable, and the
only alternative to this script is re-reading the working copy — expensive enough
that the rule would go unobeyed.

These run the script rather than asserting prose about it, for the reason
`test_coverage_check.py` gives. What is defended is exactness in both
directions: a scenario that consumed a superseded version must be returned, and
one that did not must be left alone. Returning too many re-does delivered work;
returning too few keeps a test built on a ruling since overturned in the
delivered count.
"""

import subprocess
import sys
import textwrap

import pytest

from support import PLUGIN_ROOT

SCRIPT = PLUGIN_ROOT / "scripts" / "invalidated_scenarios.py"

STEP_MAP = """\
# Step Map

| Source Step | Occurrences | Source | Parameter shapes | Expression | Status | Version |
|---|---|---|---|---|---|---|
| `I am signed in` | 4 | `LoginPage.signIn` | none | `signIn()` | reviewed | 3 |
| `I search for a record` | 4 | `SearchPage.search` | one record | `search()` | reviewed | 1 |
| `I sign out` | 3 | `LoginPage.signOut` | none | `signOut()` | reviewed | 1 |
"""

SCENARIOS = """\
# Scenarios

| Scenario | Source Steps reached | Status | Reason |
|---|---|---|---|
| `Sign in and search` | `I am signed in`, `I search for a record` | done | |
| `Sign out` | `I sign out` | done | |
| `Archive` | `I search for a record` | pending | |
"""

ASSEMBLED = """\
# Assembled

| Scenario | Test | Row versions consumed | Assembled |
|---|---|---|---|
| `Sign in and search` | `sign-in-and-search.sigma` | `I am signed in`@1, `I search for a record`@1 | 2026-09-01 |
| `Sign out` | `sign-out.sigma` | `I sign out`@1 | 2026-09-02 |
"""


def write(tmp_path, scenarios=SCENARIOS, step_map=STEP_MAP, assembled=ASSEMBLED):
    migration = tmp_path / ".testsigma" / "migration"
    migration.mkdir(parents=True, exist_ok=True)
    for name, text in (
        ("scenarios.md", scenarios),
        ("step-map.md", step_map),
        ("assembled.md", assembled),
    ):
        (migration / name).write_text(textwrap.dedent(text), encoding="utf-8")
    return migration


def run(tmp_path, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--suite", str(tmp_path), *args],
        capture_output=True, text=True,
    )


class TestTheInvalidationSet:
    def test_a_scenario_that_consumed_a_superseded_version_is_returned(self, tmp_path):
        # `I am signed in` is at version 3; the assembled test consumed 1.
        write(tmp_path)
        result = run(tmp_path)
        assert result.returncode == 1, result.stdout
        assert "Sign in and search" in result.stdout

    def test_a_scenario_whose_versions_are_current_is_left_alone(self, tmp_path):
        # Exactness in the other direction: re-opening a test nobody overturned
        # re-does delivered work and moves the delivered count backwards for
        # nothing.
        write(tmp_path)
        result = run(tmp_path)
        assert "Sign out" not in result.stdout, (
            "a scenario consuming only current versions must not be returned"
        )

    def test_nothing_superseded_is_reported_as_nothing_and_exits_zero(self, tmp_path):
        write(tmp_path, step_map=STEP_MAP.replace("| `I am signed in` | 4 | `LoginPage.signIn` | none | `signIn()` | reviewed | 3 |",
                                                  "| `I am signed in` | 4 | `LoginPage.signIn` | none | `signIn()` | reviewed | 1 |"))
        result = run(tmp_path)
        assert result.returncode == 0, result.stdout
        assert "Sign in and search" not in result.stdout

    def test_a_row_the_working_copy_never_consumed_returns_nobody(self, tmp_path):
        # A row bumped before any test used it has no dependents, and inventing
        # some would re-open scenarios on a row they never saw.
        step_map = STEP_MAP + "| `I print the batch` | 1 | `PrintPage.print` | none | `print()` | reviewed | 9 |\n"
        write(tmp_path, step_map=step_map)
        result = run(tmp_path)
        assert "print" not in result.stdout.lower()

    def test_a_version_ahead_of_the_row_is_reported_rather_than_ignored(self, tmp_path):
        # An assembled test recording a version the Step Map does not have is a
        # directory somebody edited by hand. Silence would let it stand.
        assembled = ASSEMBLED.replace("`I sign out`@1", "`I sign out`@7")
        write(tmp_path, assembled=assembled)
        result = run(tmp_path)
        assert result.returncode == 1
        assert "7" in result.stdout and "sign out" in result.stdout.lower()

    def test_a_consumed_row_the_step_map_no_longer_holds_is_reported(self, tmp_path):
        assembled = ASSEMBLED.replace("`I sign out`@1", "`I was deleted`@1")
        write(tmp_path, assembled=assembled)
        result = run(tmp_path)
        assert result.returncode == 1
        assert "I was deleted" in result.stdout


class TestWhatItSaysAndToWhom:
    def test_it_names_the_row_and_both_versions(self, tmp_path):
        # "Re-opened because a decision changed" is not actionable; which
        # decision, and how far behind, is.
        write(tmp_path)
        out = run(tmp_path).stdout
        assert "I am signed in" in out
        assert "1" in out and "3" in out

    def test_it_carries_none_of_the_forbidden_detail(self, tmp_path):
        # `references/asking.md` covers everything put in front of the Operator,
        # and this output is read out to them.
        write(tmp_path)
        out = run(tmp_path).stdout
        for forbidden in (".testsigma/migration", "Traceback", ".py"):
            assert forbidden not in out, f"the report carries {forbidden!r}"


class TestReturningThemToPending:
    def test_it_reports_without_writing_unless_asked(self, tmp_path):
        migration = write(tmp_path)
        before = (migration / "scenarios.md").read_text(encoding="utf-8")
        run(tmp_path)
        assert (migration / "scenarios.md").read_text(encoding="utf-8") == before, (
            "a report that rewrites the queue surprises whoever ran it to look"
        )

    def test_apply_returns_exactly_the_affected_scenarios_to_pending(self, tmp_path):
        migration = write(tmp_path)
        result = run(tmp_path, "--apply")
        after = (migration / "scenarios.md").read_text(encoding="utf-8")
        assert "| `Sign in and search` | `I am signed in`, `I search for a record` | pending |" in after
        assert "| `Sign out` | `I sign out` | done |" in after, (
            "a scenario nobody superseded must keep its status"
        )
        # Zero: the work was done. A Conversion runs this as a step, and a
        # non-zero exit from a step that succeeded reads as a failed gate.
        assert result.returncode == 0, result.stdout

    def test_apply_gives_the_reason_in_the_operators_terms(self, tmp_path):
        migration = write(tmp_path)
        run(tmp_path, "--apply")
        after = (migration / "scenarios.md").read_text(encoding="utf-8")
        row = [line for line in after.split("\n") if "Sign in and search" in line][0]
        assert "I am signed in" in row, "the re-opened row must say which decision changed"

    def test_apply_leaves_a_parked_scenario_parked(self, tmp_path):
        # Parking waits on the Operator; a superseded row does not clear that,
        # and overwriting the status would lose what it waits on.
        scenarios = SCENARIOS.replace(
            "| `Sign in and search` | `I am signed in`, `I search for a record` | done | |",
            "| `Sign in and search` | `I am signed in`, `I search for a record` | parked | Waiting on which Submit is live |",
        )
        migration = write(tmp_path, scenarios=scenarios)
        run(tmp_path, "--apply")
        after = (migration / "scenarios.md").read_text(encoding="utf-8")
        assert "parked" in after and "Waiting on which Submit is live" in after


class TestWhatItWillNotReopen:
    """Re-opening is for a decision that changed, not for a puzzling row.

    Converting a scenario again cannot fix a directory that says something
    impossible, and doing it anyway re-does delivered work on a guess about
    what somebody meant.
    """

    def test_a_version_ahead_of_the_row_is_reported_and_left_alone(self, tmp_path):
        migration = write(tmp_path, assembled=ASSEMBLED.replace(
            "`I sign out`@1", "`I sign out`@7"))
        result = run(tmp_path, "--apply")
        after = (migration / "scenarios.md").read_text(encoding="utf-8")
        assert "| `Sign out` | `I sign out` | done |" in after
        assert result.returncode == 1, "an unexplained row must not read as clean"

    def test_a_row_the_step_map_no_longer_holds_is_reported_and_left_alone(self, tmp_path):
        migration = write(tmp_path, assembled=ASSEMBLED.replace(
            "`I sign out`@1", "`I was deleted`@1"))
        run(tmp_path, "--apply")
        after = (migration / "scenarios.md").read_text(encoding="utf-8")
        assert "| `Sign out` | `I sign out` | done |" in after


class TestItWritesByHeaderRatherThanByPosition:
    def test_a_row_missing_its_trailing_reason_cell_is_still_re_opened(self, tmp_path):
        # An editor routinely drops a trailing empty cell, and writing by index
        # crashed on it — after the report had printed, so whoever ran it
        # believed it had applied.
        scenarios = SCENARIOS.replace(
            "| `Sign in and search` | `I am signed in`, `I search for a record` | done | |",
            "| `Sign in and search` | `I am signed in`, `I search for a record` | done |")
        migration = write(tmp_path, scenarios=scenarios)
        result = run(tmp_path, "--apply")
        assert result.returncode == 0, result.stdout + result.stderr
        after = (migration / "scenarios.md").read_text(encoding="utf-8")
        assert "| `Sign in and search` | `I am signed in`, `I search for a record` | pending |" in after

    def test_a_column_added_ahead_of_status_is_not_mis_targeted(self, tmp_path):
        scenarios = """\
        # Scenarios

        | Scenario | Owner | Source Steps reached | Status | Reason |
        |---|---|---|---|---|
        | `Sign in and search` | Priya | `I am signed in` | done | |
        | `Sign out` | Sam | `I sign out` | done | |
        """
        migration = write(tmp_path, scenarios=scenarios)
        run(tmp_path, "--apply")
        after = (migration / "scenarios.md").read_text(encoding="utf-8")
        assert "| `Sign in and search` | Priya | `I am signed in` | pending |" in after
        assert "Priya" in after and "Sam" in after, "a person's column must survive"

    def test_an_existing_reason_is_kept_after_the_one_written(self, tmp_path):
        scenarios = SCENARIOS.replace(
            "| `Sign in and search` | `I am signed in`, `I search for a record` | done | |",
            "| `Sign in and search` | `I am signed in`, `I search for a record` | done | Checked by Priya |")
        migration = write(tmp_path, scenarios=scenarios)
        run(tmp_path, "--apply")
        after = (migration / "scenarios.md").read_text(encoding="utf-8")
        assert "Checked by Priya" in after, "whoever wrote that meant it"
        assert "Re-opened" in after


class TestWhenTheDirectoryIsNotThere:
    @pytest.mark.parametrize("missing", ["scenarios.md", "step-map.md", "assembled.md"])
    def test_a_missing_file_is_reported_rather_than_read_as_nothing_to_do(
        self, tmp_path, missing
    ):
        migration = write(tmp_path)
        (migration / missing).unlink()
        result = run(tmp_path)
        assert result.returncode == 1
        assert missing in result.stdout

    def test_an_empty_assembled_table_means_no_dependents_and_not_an_error(self, tmp_path):
        write(tmp_path, assembled="# Assembled\n\n| Scenario | Test | Row versions consumed | Assembled |\n|---|---|---|---|\n")
        result = run(tmp_path)
        assert result.returncode == 0
