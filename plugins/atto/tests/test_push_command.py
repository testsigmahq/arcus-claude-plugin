# plugins/atto/tests/test_push_command.py
import json
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
CMD = PLUGIN / "commands" / "push.md"
REPO = PLUGIN.parents[1]  # repo root (…/atto-claude-plugin)


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
    assert "testsigma code push" in body
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
    # It should not pass --session-id / --project-id to code push (CLI/server own those).
    assert "do **not** pass `--session-id`" in body
    assert "do **not** pass `--project-id`" in body


def test_version_bumped():
    pj = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    assert pj["version"] == "0.4.0"


def test_help_and_readme_mention_the_command():
    assert "/atto:push" in (PLUGIN / "commands" / "help.md").read_text()
    assert "/atto:push" in (REPO / "README.md").read_text()
