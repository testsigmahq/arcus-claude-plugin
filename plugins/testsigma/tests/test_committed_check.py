"""The commit gate, and the path it watches.

Two stages instruct a Migration to commit as it goes, and a measured run
followed both and committed nothing. The instruction was not the problem: an
instruction a reader believes they followed is not a check.

The gate then reproduced the fault class it exists to catch. It watched a
hardcoded `tests/testsigma`; a run that wrote to a sibling directory got
"2 files exist only in the working tree" while more than forty untracked .sigma
files sat outside everything it looked at. ADR-0011 makes the path a recorded
fact and these tests hold the gate to reading it.

This file exists because there were no tests for this script at all, which is
how the hardcoded path survived being wrong on a live run.
"""

import subprocess
import sys

import pytest

from support import PLUGIN_ROOT

SCRIPT = PLUGIN_ROOT / "scripts" / "check_committed.py"


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, check=True)


@pytest.fixture
def suite(tmp_path):
    """A committed suite with a Migration Directory, and nothing dirty."""
    root = tmp_path / "suite"
    (root / ".testsigma" / "migration").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    (root / ".testsigma" / "migration" / "migration.md").write_text(
        "# Migration\nWorking copy: tests/testsigma\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "start")
    return root


def run(root):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--suite", str(root)],
        capture_output=True, text=True)


def record(root, path):
    """Rewrite migration.md's Working copy line, and commit it.

    Committing matters: an uncommitted migration.md is itself dirty, and a test
    asserting a clean tree would pass or fail on that rather than on the thing
    it is about.
    """
    marker = root / ".testsigma" / "migration" / "migration.md"
    marker.write_text(f"# Migration\nWorking copy: {path}\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "record")


def dirty_at(root, relative):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("test \"T\" {}\n", encoding="utf-8")


def test_a_clean_tree_passes(suite):
    result = run(suite)
    assert result.returncode == 0, result.stdout


def test_an_uncommitted_migration_directory_fails(suite):
    dirty_at(suite, ".testsigma/migration/step-map.md")
    result = run(suite)
    assert result.returncode == 1
    assert "step-map.md" in result.stdout


def test_it_watches_the_recorded_working_copy(suite):
    dirty_at(suite, "tests/testsigma/a.test.sigma")
    result = run(suite)
    assert result.returncode == 1
    assert "a.test.sigma" in result.stdout


def test_it_watches_a_working_copy_that_is_not_the_default(suite):
    # The measured failure. A Migration recording a different path must be
    # watched at that path, or the gate reports a clean tree over an entirely
    # untracked working copy.
    record(suite, "automation/sigma")
    dirty_at(suite, "automation/sigma/a.test.sigma")
    result = run(suite)
    assert result.returncode == 1, (
        f"the gate missed a working copy at the recorded path: {result.stdout}"
    )
    assert "a.test.sigma" in result.stdout


def test_a_recorded_path_replaces_the_default_rather_than_adding_to_it(suite):
    # Watching both would make the gate pass its own test while still being
    # unable to find a real Migration's work, since the default would catch the
    # common case and hide the bug.
    record(suite, "automation/sigma")
    dirty_at(suite, "tests/testsigma/stray.test.sigma")
    result = run(suite)
    assert result.returncode == 0, (
        "the gate is watching the default as well as the recorded path, so a "
        f"wrong recorded path would still look clean: {result.stdout}"
    )


class TestAnUnrecordedPath:
    """A missing line is reported, never silently defaulted.

    Guessing right on this machine is what hides the problem from the session
    that guesses differently, which is the whole failure ADR-0011 addresses.
    """

    def _unrecord(self, suite):
        marker = suite / ".testsigma" / "migration" / "migration.md"
        marker.write_text("# Migration\n", encoding="utf-8")
        git(suite, "add", "-A")
        git(suite, "commit", "-qm", "unrecord")

    def test_it_says_the_line_is_missing(self, suite):
        self._unrecord(suite)
        assert "no 'Working copy:' line" in run(suite).stdout

    def test_a_skeleton_placeholder_is_not_a_recorded_decision(self, suite):
        record(suite, "<path, relative to the suite root>")
        assert "no 'Working copy:' line" in run(suite).stdout

    def test_it_still_checks_the_default_so_the_gate_is_not_disabled(self, suite):
        self._unrecord(suite)
        dirty_at(suite, "tests/testsigma/a.test.sigma")
        assert run(suite).returncode == 1


def test_a_directory_that_is_not_a_repository_fails_rather_than_passing(tmp_path):
    # The sibling layout's first consequence: not a git repository at all. A
    # gate that cannot read history must not report a clean tree.
    (tmp_path / ".testsigma" / "migration").mkdir(parents=True)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "git status" in result.stdout
