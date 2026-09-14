"""The bump rule, checked rather than asserted in prose.

A row's `Version` is what makes a corrected decision findable: `assembled.md`
records what each delivered test consumed, so a test behind the row's current
version was built on a ruling since overturned. A row re-decided without a bump
is invisible — the tests built on the old ruling keep their place in the
delivered count and nothing says otherwise.

The converse matters as much. Occurrence counts and provenance change on nearly
every Conversion, and a version that moved on one of those returns scenarios to
the queue and rebuilds their tests for nothing.

Prior art for driving git from a test: `test_committed_check.py`.
"""

import subprocess
import sys

import pytest

from support import PLUGIN_ROOT

SCRIPT = PLUGIN_ROOT / "scripts" / "check_row_versions.py"

HEADER = """\
# Step Map

| Source Step | Occurrences | Source | Parameter shapes | Expression | Status | Version |
|---|---|---|---|---|---|---|
"""

ROW = "| `I am signed in` | 4 | `LoginPage.signIn` | none | `signIn()` | reviewed | 1 |\n"


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, check=True)


@pytest.fixture
def suite(tmp_path):
    """A suite whose Step Map is committed, holding one reviewed row."""
    root = tmp_path / "suite"
    (root / ".testsigma" / "migration").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    write(root, HEADER + ROW)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "start")
    return root


def write(root, text):
    (root / ".testsigma" / "migration" / "step-map.md").write_text(
        text, encoding="utf-8")


def run(root):
    return subprocess.run([sys.executable, str(SCRIPT), "--suite", str(root)],
                          capture_output=True, text=True)


def test_an_unchanged_step_map_passes(suite):
    assert run(suite).returncode == 0


class TestARowDecidedAgain:
    def test_a_changed_expression_without_a_bump_is_rejected(self, suite):
        write(suite, HEADER + ROW.replace("`signIn()`", "`signIn(user)`"))
        result = run(suite)
        assert result.returncode == 1
        assert "I am signed in" in result.stdout

    def test_a_changed_status_without_a_bump_is_rejected(self, suite):
        write(suite, HEADER + ROW.replace("| reviewed |", "| residue |"))
        assert run(suite).returncode == 1

    def test_a_changed_expression_with_a_bump_passes(self, suite):
        write(suite, HEADER + ROW.replace("`signIn()`", "`signIn(user)`").replace(
            "| reviewed | 1 |", "| reviewed | 2 |"))
        result = run(suite)
        assert result.returncode == 0, result.stdout


class TestARowMerelyCorrected:
    def test_a_changed_occurrence_count_needs_no_bump(self, suite):
        # Occurrences change as new scenarios reach the row, on nearly every
        # Conversion.
        write(suite, HEADER + ROW.replace("| 4 |", "| 9 |"))
        assert run(suite).returncode == 0

    def test_a_bump_with_no_change_of_decision_is_rejected(self, suite):
        # It returns scenarios to the queue and rebuilds their tests for a
        # correction nobody built anything on.
        write(suite, HEADER + ROW.replace("| reviewed | 1 |", "| reviewed | 2 |"))
        result = run(suite)
        assert result.returncode == 1
        assert "I am signed in" in result.stdout

    def test_a_corrected_provenance_needs_no_bump(self, suite):
        write(suite, HEADER + ROW.replace("`LoginPage.signIn`", "`SessionPage.signIn`"))
        assert run(suite).returncode == 0


class TestRowsWithNothingToCompare:
    def test_a_new_row_is_not_a_fault(self, suite):
        write(suite, HEADER + ROW + "| `I sign out` | 1 | `LoginPage.signOut` | none | `signOut()` | reviewed | 1 |\n")
        assert run(suite).returncode == 0

    def test_a_removed_row_is_not_a_fault(self, suite):
        write(suite, HEADER)
        assert run(suite).returncode == 0


class TestWhenItCannotCompare:
    def test_a_missing_step_map_is_reported(self, suite):
        (suite / ".testsigma" / "migration" / "step-map.md").unlink()
        result = run(suite)
        assert result.returncode == 1
        assert "step-map.md" in result.stdout

    def test_an_uncommitted_step_map_is_said_so_rather_than_passed_silently(self, tmp_path):
        root = tmp_path / "suite"
        (root / ".testsigma" / "migration").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        write(root, HEADER + ROW)
        result = run(root)
        assert result.returncode == 0
        assert "not been committed" in result.stdout
