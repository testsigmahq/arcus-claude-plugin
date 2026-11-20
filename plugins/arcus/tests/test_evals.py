"""The eval cases are documents too. The runner is loud about few mistakes and silent about the rest, so check the shape."""

import subprocess

import pytest

from support import PLUGIN_ROOT, frontmatter

EVALS = PLUGIN_ROOT / "evals"
CASES = sorted(p for p in EVALS.iterdir() if p.is_dir())
GRADER_TYPES = {"regex", "tool_order", "tool_used", "file_exists", "llm", "baseline"}
PROMPT_KEYS = {"name", "tags", "runs", "max_turns", "allowed_tools", "timeout_seconds"}


def test_there_are_cases():
    assert len(CASES) >= 5


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
def test_a_case_has_every_part_and_its_name_is_its_folder(case):
    for part in ("case.yaml", "prompt.md", "scaffold.sh"):
        assert (case / part).is_file(), f"{case.name} has no {part}"
    assert f"name: {case.name}\n" in (case / "case.yaml").read_text()
    assert frontmatter(case / "prompt.md")["name"] == case.name


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
def test_a_prompt_uses_only_keys_the_runner_knows(case):
    assert set(frontmatter(case / "prompt.md")) <= PROMPT_KEYS


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
def test_a_case_has_graders_of_known_types_and_one_routing_check(case):
    graders = sorted((case / "graders").glob("*.md"))
    assert graders, f"{case.name} has no graders"
    types = [frontmatter(g)["type"] for g in graders]
    assert set(types) <= GRADER_TYPES
    assert "tool_used" in types, f"{case.name} does not check that a skill was used"


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
def test_a_scaffold_is_valid_bash(case):
    result = subprocess.run(["bash", "-n", str(case / "scaffold.sh")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
def test_a_scaffold_builds_a_repo_the_cli_can_bind(case, tmp_path):
    subprocess.run(["bash", str(case / "scaffold.sh")], cwd=tmp_path, check=True, capture_output=True)
    assert (tmp_path / "arcus.json").is_file()
    assert (tmp_path / "tests" / "arcus" / "demo" / "tests").is_dir()
