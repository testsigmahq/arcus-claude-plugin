import shutil
import subprocess

import pytest

from support import CLI_SURFACE, GLOBAL_FLAGS, cli_uses, markdown_files, read


@pytest.mark.parametrize("doc", markdown_files(), ids=lambda p: p.name)
def test_documents_name_only_commands_and_options_the_cli_has(doc):
    for command, flags in cli_uses(read(doc)):
        unknown = flags - CLI_SURFACE[command] - GLOBAL_FLAGS
        assert not unknown, f"{doc.name}: `arcus {command}` has no option {sorted(unknown)}"


def test_the_documents_use_the_commands_the_flow_needs():
    used = {command for doc in markdown_files() for command, _ in cli_uses(read(doc))}
    assert {"auth status", "init", "docs", "check", "fmt", "push"} <= used


@pytest.mark.skipif(shutil.which("arcus") is None, reason="no arcus CLI on PATH")
@pytest.mark.parametrize("command", sorted(CLI_SURFACE))
def test_the_surface_matches_a_real_cli(command):
    """The table in support.py is only as good as it is true. Ask the CLI."""
    help_text = subprocess.run(["arcus", *command.split(), "--help"], capture_output=True, text=True, timeout=60).stdout
    for flag in CLI_SURFACE[command]:
        assert flag in help_text, f"`arcus {command}` has no {flag}"
