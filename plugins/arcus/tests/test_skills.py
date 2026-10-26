import re

import pytest

from support import COMMANDS_DIR, REPO_ROOT, SKILL_MAX_LINES, SKILLS, SKILLS_DIR, frontmatter, read, skill_path


def test_the_skills_are_the_expected_ones():
    assert sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir()) == sorted(SKILLS)


@pytest.mark.parametrize("name", SKILLS)
def test_a_skill_has_a_name_and_a_description_that_says_when(name):
    meta = frontmatter(skill_path(name))
    assert meta["name"] == name
    assert meta["description"].startswith("Use when")


@pytest.mark.parametrize("name", SKILLS)
def test_a_skill_stays_inside_its_size_budget(name):
    assert len(read(skill_path(name)).splitlines()) <= SKILL_MAX_LINES


@pytest.mark.parametrize("name", SKILLS)
def test_a_skill_holds_no_copy_of_the_language(name):
    """The CLI carries the catalogue. A fenced sigma example here would be a stale copy of it."""
    text = read(skill_path(name))
    assert not re.search(r"^```sigma", text, re.M)


@pytest.mark.parametrize("name", SKILLS)
def test_help_and_readme_list_every_skill(name):
    for doc in (COMMANDS_DIR / "help.md", REPO_ROOT / "README.md"):
        assert f"/arcus:{name}" in read(doc), f"{doc.name} does not list /arcus:{name}"


def test_push_asks_for_a_dry_run_before_it_pushes():
    text = read(skill_path("push"))
    assert text.index("arcus push --dry-run") < text.index("arcus push --json")
    assert "Push without a dry run" in text


def test_author_lets_the_check_decide():
    text = read(skill_path("author"))
    assert "arcus check" in text and "arcus docs" in text
    assert "Do not make the check pass by making the test weaker" in text


def test_nobody_but_the_user_signs_in():
    assert "You never sign the user in" in read(skill_path("setup"))
    assert "Never sign the user in" in read(skill_path("push"))
