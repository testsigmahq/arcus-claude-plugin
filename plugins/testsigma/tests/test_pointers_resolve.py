"""Every pointer into the plugin's own files resolves, and is spelled one way.

A pointer from a skill to a reference is a seam, and until this module the suite
could not see across one: every pointer test asserted the *substring*
`references/foo.md`, which `../../references/foo.md` also contains. So three
spellings coexisted, one of them resolving nowhere, and 753 tests passed.

`${CLAUDE_PLUGIN_ROOT}` is substituted with the plugin's absolute path when a
component file is loaded, which is why it is the spelling Claude Code's own
plugin-structure guidance gives for commands, agents and skills — and why a
bare `references/foo.md` is wrong here: bare means skill-relative, and this
plugin's references sit at the plugin root, shared (ADR-0007).
"""

import re

import pytest

from support import (
    MIGRATION_DIRECTORY_FILES,
    PLUGIN_ROOT,
    command_files,
    skill_files,
)

#: The plugin's own directories. A closed set, so this needs no allowlist of
#: the *other* kind of path these documents name — the Migration Directory
#: files, which live in the user's suite and must never be resolved here.
PLUGIN_DIRECTORIES = ("references", "adapters", "scripts", "tests", "docs", "evals")

ANCHOR = "${CLAUDE_PLUGIN_ROOT}"

#: A path into a plugin directory, wherever it appears.
_PLUGIN_PATH = re.compile(
    r"(?P<prefix>\S*?)(?P<path>(?:" + "|".join(PLUGIN_DIRECTORIES) + r")/[\w./-]+)"
)

COMPONENTS = sorted(skill_files()) + sorted(command_files())


def _ids(path):
    return f"{path.parent.name}/{path.name}"


def _pointers(path):
    """Every plugin-directory path in the document, with what precedes it."""
    return [
        (match.group("prefix"), match.group("path"))
        for match in _PLUGIN_PATH.finditer(path.read_text(encoding="utf-8"))
    ]


@pytest.mark.parametrize("component", COMPONENTS, ids=_ids)
def test_every_pointer_is_anchored_to_the_plugin_root(component):
    # The three spellings that were in use: anchored (correct), `../../` from a
    # skill (worked, but only because the reader infers the anchor), and bare
    # (resolves to a directory no skill has). Anchoring is the spelling Claude
    # Code substitutes, so it is the one that cannot be misread.
    unanchored = [
        prefix + path
        for prefix, path in _pointers(component)
        if not prefix.endswith(ANCHOR + "/")
    ]
    assert not unanchored, (
        f"{_ids(component)} names plugin files without anchoring them to "
        f"{ANCHOR}: {unanchored}"
    )


@pytest.mark.parametrize("component", COMPONENTS, ids=_ids)
def test_every_pointer_resolves_to_a_file_that_exists(component):
    # The check the suite never had. Three of the broken pointers were the
    # CLI-probe instruction on the critical path of both entry points, where a
    # failed read is a silently skipped probe rather than an error.
    missing = [
        path
        for _, path in _pointers(component)
        if not (PLUGIN_ROOT / path).exists()
    ]
    assert not missing, f"{_ids(component)} points at files that do not exist: {missing}"


@pytest.mark.parametrize("component", COMPONENTS, ids=_ids)
def test_the_glossary_is_anchored_too(component):
    # `CONTEXT.md` sits at the plugin root like the references do, and was
    # named bare in all five skills and the command.
    body = component.read_text(encoding="utf-8")
    if "CONTEXT.md" not in body:
        pytest.skip("this component does not name the glossary")
    for match in re.finditer(r"(\S*?)CONTEXT\.md", body):
        assert match.group(1).endswith(ANCHOR + "/"), (
            f"{_ids(component)} names CONTEXT.md unanchored: {match.group(0)!r}"
        )


@pytest.mark.parametrize("component", COMPONENTS, ids=_ids)
def test_a_migration_directory_file_is_never_anchored_to_the_plugin(component):
    # The inverse error, and the reason this module does not simply resolve
    # everything path-shaped: `residue.md` and `step-map.md` live in the user's
    # suite. Anchoring one to the plugin would point a stage at a file the
    # plugin ships and the Migration does not own.
    body = component.read_text(encoding="utf-8")
    for filename in MIGRATION_DIRECTORY_FILES:
        assert f"{ANCHOR}/{filename}" not in body, (
            f"{_ids(component)} anchors {filename} to the plugin; it belongs to "
            f"the source suite"
        )


def test_the_shared_references_layout_is_recorded_as_a_decision():
    # Claude Code's documented layout puts a skill's `references/` inside the
    # skill. This plugin puts them at the plugin root and shares them, which is
    # why a bare `references/foo.md` resolves nowhere here — and a reviewer
    # reading the convention will call the layout a mistake unless the reason
    # is written down. One already did.
    from support import adr_files

    matching = [p for p in adr_files() if p.name.startswith("0007")]
    assert len(matching) == 1, f"no ADR-0007 among {[p.name for p in adr_files()]}"
    body = matching[0].read_text(encoding="utf-8").lower()
    assert "plugin root" in body
    assert "duplicat" in body, (
        "the trade-off is what per-skill references would force, and that is "
        "the whole reason for the deviation"
    )
    assert "scripts/" in body, (
        "the sanctioned precedent — a shared scripts/ at the plugin root — is "
        "what makes this a deviation in placement rather than in kind"
    )
