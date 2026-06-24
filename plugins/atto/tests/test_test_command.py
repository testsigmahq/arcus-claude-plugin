# plugins/atto/tests/test_test_command.py
import json
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
CMD = PLUGIN / "commands" / "test.md"
REPO = PLUGIN.parents[1]  # repo root (…/atto-claude-plugin)


def test_command_exists_with_description_and_invokes_skill():
    assert CMD.exists(), f"{CMD} missing"
    text = CMD.read_text()
    assert text.startswith("---\n"), "missing frontmatter"
    _, fm, body = text.split("---\n", 2)
    assert any(line.strip().startswith("description:") for line in fm.splitlines())
    # The command is a doorway: it must invoke the skill by name.
    assert "testsigma-tests" in body


def test_version_bumped():
    pj = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    assert pj["version"] == "0.4.0"


def test_help_and_readme_mention_the_command():
    assert "/atto:test" in (PLUGIN / "commands" / "help.md").read_text()
    assert "/atto:test" in (REPO / "README.md").read_text()
