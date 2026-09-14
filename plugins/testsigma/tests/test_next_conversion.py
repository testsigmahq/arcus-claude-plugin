"""Choosing the next Conversion: greedy set cover over `scenarios.md`.

These run the script rather than asserting prose about it, for the reason
`test_coverage_check.py` gives: a check whose own tests only read the document
describing it passes while the mechanism is broken.

What is being defended is mostly determinism. Two sessions reading the same
Migration Directory must select the same scenario — including at a tie, where
"whatever came first" is a different answer every time a row moves.
"""

import subprocess
import sys
import textwrap

import pytest

from support import PLUGIN_ROOT

SCRIPT = PLUGIN_ROOT / "scripts" / "next_conversion.py"

STEP_MAP = """\
# Step Map

| Source Step | Occurrences | Source | Parameter shapes | Expression | Status | Version |
|---|---|---|---|---|---|---|
| `I am signed in` | 4 | `LoginPage.signIn` | none | `signIn()` | reviewed | 1 |
| `I search for record "<param>"` | 4 | `SearchPage.search` | one record | | unreviewed | 1 |
| `I archive the record` | 2 | `JournalPage.archive` | none | | unreviewed | 1 |
| `I print the batch` | 1 | `PrintPage.print` | none | | unreviewed | 1 |
| `I sign out` | 3 | `LoginPage.signOut` | none | `signOut()` | reviewed | 1 |
"""


def write(tmp_path, scenarios, step_map=STEP_MAP):
    migration = tmp_path / ".testsigma" / "migration"
    migration.mkdir(parents=True, exist_ok=True)
    (migration / "scenarios.md").write_text(
        textwrap.dedent(scenarios), encoding="utf-8")
    (migration / "step-map.md").write_text(step_map, encoding="utf-8")
    return tmp_path


def run(suite, extra=()):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--suite", str(suite), *extra],
        capture_output=True, text=True,
    )


HEADER = """\
    # Scenarios

    | Scenario | Source Steps reached | Status | Reason |
    |---|---|---|---|
"""


def scenarios(*rows):
    return HEADER + "".join("    " + r + "\n" for r in rows)


class TestItSelectsByUnseenSourceSteps:
    def test_it_picks_the_scenario_introducing_the_most(self, tmp_path):
        suite = write(tmp_path, scenarios(
            "| `Sign in and out` | `I am signed in`, `I sign out` | pending | |",
            "| `Archive a record` | `I am signed in`, `I search for record \"<param>\"`, "
            "`I archive the record` | pending | |",
        ))
        result = run(suite)
        assert result.returncode == 0, result.stdout
        assert "next:         Archive a record" in result.stdout
        assert "introduces:   2 unseen" in result.stdout

    def test_a_step_the_map_has_judged_counts_as_seen(self, tmp_path):
        # `I am signed in` is reviewed, so a scenario reaching only it
        # introduces nothing and teaches the Migration nothing.
        suite = write(tmp_path, scenarios(
            "| `Sign in` | `I am signed in` | pending | |",
            "| `Print` | `I print the batch` | pending | |",
        ))
        assert "next:         Print" in run(suite).stdout

    def test_a_step_absent_from_the_map_counts_as_unseen(self, tmp_path):
        # Not in the Step Map is certainly not judged. Scoring it as seen would
        # hide a scenario the Migration knows least about.
        suite = write(tmp_path, scenarios(
            "| `Sign in` | `I am signed in` | pending | |",
            "| `New ground` | `I do something nobody enumerated` | pending | |",
        ))
        assert "next:         New ground" in run(suite).stdout

    def test_a_step_written_twice_is_counted_once(self, tmp_path):
        # Counting occurrences would rank a repetitive scenario above one that
        # actually teaches more.
        suite = write(tmp_path, scenarios(
            "| `Repeats` | `I archive the record`, `I archive the record` | pending | |",
            "| `Teaches` | `I search for record \"<param>\"`, `I print the batch` | pending | |",
        ))
        out = run(suite).stdout
        assert "next:         Teaches" in out
        assert "introduces:   2 unseen" in out

    def test_a_comma_inside_a_step_does_not_split_it(self, tmp_path):
        # Backticks delimit; commas do not. A step holding a comma scored as two
        # would over-count what its scenario introduces.
        suite = write(tmp_path, scenarios(
            '| `Commas` | `I enter "a, b" in the field` | pending | |',
            "| `Two steps` | `I search for record \"<param>\"`, `I print the batch` | pending | |",
        ))
        out = run(suite).stdout
        assert "next:         Two steps" in out


class TestItSelectsOnlyPendingScenarios:
    def test_an_out_of_scope_scenario_is_never_selected(self, tmp_path):
        # It was screened and ruled out. Selecting it would convert what
        # somebody already established cannot be converted.
        suite = write(tmp_path, scenarios(
            "| `Ruled out` | `I search for record \"<param>\"`, `I archive the record`, "
            "`I print the batch` | out-of-scope | drives a spreadsheet |",
            "| `Convertible` | `I print the batch` | pending | |",
        ))
        out = run(suite).stdout
        assert "next:         Convertible" in out
        assert "Ruled out" not in out.split("next:")[1]

    def test_a_parked_scenario_is_not_selected_while_parked(self, tmp_path):
        # It is waiting on the Operator. Taking it again before the answer
        # arrives is the stall that parking exists to prevent.
        suite = write(tmp_path, scenarios(
            "| `Waiting` | `I search for record \"<param>\"`, `I archive the record`, "
            "`I print the batch` | parked | needs a login the Operator must supply |",
            "| `Ready` | `I print the batch` | pending | |",
        ))
        assert "next:         Ready" in run(suite).stdout

    def test_a_done_scenario_is_not_selected_again(self, tmp_path):
        suite = write(tmp_path, scenarios(
            "| `Delivered` | `I search for record \"<param>\"`, `I archive the record`, "
            "`I print the batch` | done | |",
            "| `Ready` | `I print the batch` | pending | |",
        ))
        assert "next:         Ready" in run(suite).stdout

    def test_nothing_pending_is_reported_rather_than_inferred(self, tmp_path):
        suite = write(tmp_path, scenarios(
            "| `Delivered` | `I am signed in` | done | |",
            "| `Waiting` | `I print the batch` | parked | needs an answer |",
        ))
        result = run(suite)
        assert result.returncode == 1
        assert "No scenario is pending" in result.stdout
        # A parked scenario is taken up by answering it, not by this ordering.
        assert "parked" in result.stdout.lower()


class TestItIsDeterministic:
    TIED = (
        "| `Beta` | `I search for record \"<param>\"`, `I archive the record` | pending | |",
        "| `Alpha` | `I print the batch`, `I do something else` | pending | |",
    )

    def test_a_tie_is_broken_the_same_way_every_run(self, tmp_path):
        suite = write(tmp_path, scenarios(*self.TIED))
        first = run(suite).stdout
        assert "next:         Alpha" in first
        assert run(suite).stdout == first

    def test_the_tie_break_does_not_depend_on_row_order(self, tmp_path):
        # A row moved by an unrelated edit must not change the choice, or two
        # sessions select differently from the same state.
        a = write(tmp_path / "a", scenarios(*self.TIED))
        b = write(tmp_path / "b", scenarios(*reversed(self.TIED)))
        assert "next:         Alpha" in run(a).stdout
        assert "next:         Alpha" in run(b).stdout


class TestTheThresholdHandsOverToOperatorPriority:
    SATURATED = scenarios(
        "| `Almost done` | `I am signed in`, `I sign out`, `I print the batch` | pending | |",
    )

    def test_it_reports_the_switch_when_the_best_is_below_the_threshold(self, tmp_path):
        # One unseen step left: no order now teaches the Migration much more
        # than any other, and the Operator can start naming what they want.
        result = run(write(tmp_path, self.SATURATED))
        assert result.returncode == 0
        assert "saturated" in result.stdout.lower()
        assert "operator" in result.stdout.lower()

    def test_it_still_names_a_scenario_after_the_switch(self, tmp_path):
        # The switch changes who chooses, not whether there is an answer.
        out = run(write(tmp_path, self.SATURATED)).stdout
        assert "next:         Almost done" in out

    def test_it_says_nothing_about_a_switch_while_vocabulary_is_still_being_learned(
            self, tmp_path):
        suite = write(tmp_path, scenarios(
            "| `Teaches` | `I search for record \"<param>\"`, `I archive the record`, "
            "`I print the batch` | pending | |",
        ))
        assert "saturated" not in run(suite).stdout.lower()

    def test_the_threshold_is_settable_because_it_is_measured(self, tmp_path):
        # A fixed count guesses at a suite's shape: one flattens at the eighth
        # Conversion and another at the fortieth.
        suite = write(tmp_path, scenarios(
            "| `Teaches` | `I search for record \"<param>\"`, `I archive the record`, "
            "`I print the batch` | pending | |",
        ))
        assert "saturated" in run(suite, ("--threshold", "4")).stdout.lower()


class TestItRefusesToGuessWhenTheStateIsMissing:
    @pytest.mark.parametrize("missing", ["scenarios.md", "step-map.md"])
    def test_an_absent_file_is_reported_rather_than_treated_as_empty(
            self, tmp_path, missing):
        suite = write(tmp_path, scenarios(
            "| `Ready` | `I print the batch` | pending | |",
        ))
        (suite / ".testsigma" / "migration" / missing).unlink()
        result = run(suite)
        assert result.returncode == 1
        assert missing in result.stdout


def test_it_never_reads_a_stored_unseen_count(tmp_path):
    """A stored count is stale the moment any Conversion finishes.

    The column here is a lie, and a script trusting it would select `Lying`.
    Recomputing is the whole reason the count is not a column in the real file.
    """
    migration = tmp_path / ".testsigma" / "migration"
    migration.mkdir(parents=True)
    (migration / "scenarios.md").write_text(textwrap.dedent("""\
        # Scenarios

        | Scenario | Source Steps reached | Status | Unseen | Reason |
        |---|---|---|---|---|
        | `Lying` | `I am signed in` | pending | 99 | |
        | `Honest` | `I print the batch` | pending | 0 | |
        """), encoding="utf-8")
    (migration / "step-map.md").write_text(STEP_MAP, encoding="utf-8")
    assert "next:         Honest" in run(tmp_path).stdout
