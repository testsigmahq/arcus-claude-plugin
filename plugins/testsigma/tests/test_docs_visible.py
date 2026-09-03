"""The plugin's own glossary and ADRs must stay visible to version control.

A broad `docs/` ignore rule in the repository root once hid every ADR in this
plugin. The files were on disk, git could not see them, and nothing noticed. This
module is that fault turned into a standing check.

Two different properties are asserted, because they fail in different ways:

- git does not *ignore* the files. This is the standing property and the fault
  that actually occurred. It holds whether or not anything is committed yet.
- the files are *present in the repository*, once the plugin is committed at all.
  A file that was committed and then deleted passes the ignore check and fails
  this one. It arms itself on the first commit rather than fighting
  work-in-progress.

Only the git-dependent assertions are skipped when there is no working tree. The
existence and numbering checks need no git and must never disappear silently.
"""

import pytest

from support import (
    CONTEXT,
    MANIFEST,
    PLUGIN_ROOT,
    adr_files,
    git_ignores,
    git_tracked_paths,
    is_git_repo,
)

needs_git = pytest.mark.skipif(
    not is_git_repo(), reason="not a git working tree, so nothing can be ignored"
)


# --- these need no git and must always run ----------------------------------

def test_the_glossary_exists():
    assert CONTEXT.is_file(), "the plugin has no CONTEXT.md"


def test_there_is_at_least_one_adr():
    # Without this the parametrised checks below would pass vacuously.
    assert adr_files(), "no ADRs found; the checks below would prove nothing"


def test_adr_numbers_are_unique_and_contiguous_from_one():
    numbers = [int(path.name[:4]) for path in adr_files()]
    assert len(numbers) == len(set(numbers)), f"duplicate ADR numbers: {numbers}"
    assert numbers == list(range(1, len(numbers) + 1)), (
        f"ADR numbers must run 1..n with no gaps, got {numbers}"
    )


# --- not ignored -------------------------------------------------------------

@needs_git
def test_the_glossary_is_not_ignored():
    assert not git_ignores(CONTEXT), f"{CONTEXT.name} is ignored by git"


@needs_git
def test_the_manifest_is_not_ignored():
    assert MANIFEST.is_file(), "the plugin manifest is missing"
    assert not git_ignores(MANIFEST), "the plugin manifest is ignored by git"


@needs_git
@pytest.mark.parametrize("adr", adr_files(), ids=lambda p: p.stem.split("-")[0])
def test_each_adr_is_not_ignored(adr):
    assert not git_ignores(adr), f"{adr.name} is ignored by git"


# --- present in the repository ----------------------------------------------

@needs_git
def test_the_docs_are_in_the_repository_once_the_plugin_is_committed():
    tracked = git_tracked_paths(PLUGIN_ROOT)
    if not tracked:
        pytest.skip("plugin is not committed yet; this check arms on the first commit")
    missing = [
        path.name
        for path in [CONTEXT, MANIFEST, *adr_files()]
        if path not in tracked
    ]
    assert not missing, f"on disk but not in the repository: {missing}"
