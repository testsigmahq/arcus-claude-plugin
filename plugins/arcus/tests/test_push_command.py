# plugins/arcus/tests/test_push_command.py
import json
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
CMD = PLUGIN / "commands" / "push.md"
REPO = PLUGIN.parents[1]  # repo root (…/arcus-claude-plugin)


def test_command_exists_with_description():
    assert CMD.exists(), f"{CMD} missing"
    text = CMD.read_text()
    assert text.startswith("---\n"), "missing frontmatter"
    _, fm, _body = text.split("---\n", 2)
    assert any(line.strip().startswith("description:") for line in fm.splitlines())


def test_command_delegates_to_testsigma_cli():
    body = CMD.read_text()
    # The command is a thin doorway: it drives the testsigma CLI, not its own logic.
    assert "testsigma sprints list" in body
    assert "testsigma test push" in body
    # Both targets are offered to the user.
    assert "--sprint" in body
    assert "--unmapped" in body


def test_command_reads_pinned_project_in_preflight():
    # Must resolve the pinned project before listing sprints.
    assert "project/cli.py" in CMD.read_text()


def test_command_stays_thin():
    # Collapse whitespace so line-wrapping in the markdown doesn't break matching.
    body = " ".join(CMD.read_text().lower().split())
    # The CLI auto-detects the session; the command must say not to pass it.
    assert "auto-detect" in body
    # It should not pass --session-id to code push (the CLI owns session detection).
    assert "do **not** pass `--session-id`" in body
    # --project-id is now REQUIRED for --sprint / --unmapped, so it must be passed
    # (the old "do not pass --project-id" guidance is obsolete).
    assert "--project-id" in body
    assert "do **not** pass `--project-id`" not in body


def test_command_uses_all_push_flags():
    # /arcus:push should exercise the full `testsigma test push` surface.
    body = CMD.read_text()
    for flag in (
        "--project-id",
        "--sprint",
        "--unmapped",
        "--issue",
        "--module",
        "--priority",
        "--run-status",
        "--test-type",
    ):
        assert flag in body, f"push.md should reference {flag}"
    # --module is mandatory, so the user must be shown the modules to pick from.
    assert "testsigma modules list" in body
    # --test-type takes a name, so the valid ones must be discoverable too.
    assert "testsigma test-types list" in body
    assert "Functional" in body


def test_version_bumped():
    # /arcus:push landed in 0.5.0; assert at least that (not an exact pin) so
    # later version bumps don't break this test.
    pj = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    version = tuple(int(x) for x in pj["version"].split("."))
    assert version >= (0, 5, 0)


def test_command_lists_issues_and_passes_issue_flag():
    body = " ".join(CMD.read_text().lower().split())
    # Sprint path must let the user pick a story and pass it as --issue.
    assert "testsigma sprints issues" in body
    assert "--issue" in body


def test_help_and_readme_mention_the_command():
    assert "/arcus:push" in (PLUGIN / "commands" / "help.md").read_text()
    assert "/arcus:push" in (REPO / "README.md").read_text()


def test_push_doc_mentions_status_flag():
    body = CMD.read_text()
    assert "--run-status" in body
    assert "Passed" in body and "Failed" in body
    # Only send when the test was actually run in this session:
    lower = body.lower()
    assert (
        "if the tests were run" in lower
        or "if you ran" in lower
        or "when the test was run" in lower
    )
