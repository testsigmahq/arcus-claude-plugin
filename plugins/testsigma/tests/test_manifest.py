"""The plugin's manifest and its marketplace entry must be valid and agree.

These assert structure only. Nothing here depends on the wording of a
description or the order of keys, so rewording the manifest is never a failure.
"""

import json
import os
import re

import pytest

from support import (
    MANIFEST,
    MARKETPLACE,
    PLUGIN_ROOT,
    command_files,
    is_kebab_case,
    read_frontmatter,
    skill_files,
)

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def marketplace():
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


# --- the manifest itself -----------------------------------------------------

def test_manifest_lives_where_claude_code_looks_for_it():
    assert MANIFEST.is_file(), f"{MANIFEST} missing"


def test_manifest_is_valid_json(manifest):
    assert isinstance(manifest, dict)


def test_manifest_declares_a_kebab_case_name(manifest):
    name = manifest.get("name")
    assert name, "manifest has no name, which is the one required field"
    assert is_kebab_case(name), f"plugin name {name!r} must be kebab-case"


def test_manifest_name_matches_its_directory(manifest):
    # A mismatch installs the plugin under a name nobody expects.
    assert manifest["name"] == PLUGIN_ROOT.name


def test_version_is_semver(manifest):
    assert SEMVER.match(str(manifest.get("version", ""))), "version must be MAJOR.MINOR.PATCH"


# --- agreement with the marketplace -----------------------------------------

def test_marketplace_lists_this_plugin(manifest, marketplace):
    names = [entry.get("name") for entry in marketplace.get("plugins", [])]
    assert manifest["name"] in names, f"{manifest['name']} is not listed in the marketplace"


def test_marketplace_entry_points_at_this_directory(manifest, marketplace):
    entries = [e for e in marketplace["plugins"] if e.get("name") == manifest["name"]]
    assert len(entries) == 1, f"expected exactly one entry named {manifest['name']}, got {len(entries)}"
    source = entries[0].get("source", "")
    resolved = (MARKETPLACE.parent.parent / source).resolve()
    assert resolved == PLUGIN_ROOT, f"marketplace source {source!r} resolves to {resolved}"


# --- structural rules Claude Code enforces ----------------------------------

@pytest.mark.parametrize("component", ["commands", "agents", "skills", "hooks"])
def test_component_directories_are_not_nested_in_the_manifest_directory(component):
    # Components must sit at the plugin root. Nested ones are silently ignored.
    assert not (PLUGIN_ROOT / ".claude-plugin" / component).exists(), (
        f".claude-plugin/{component} would never be discovered; move it to the plugin root"
    )


def test_declared_component_paths_are_relative(manifest):
    for key in ("commands", "agents", "skills", "hooks", "mcpServers"):
        value = manifest.get(key)
        if value is None:
            continue
        # mcpServers may be an inline object keyed by server name rather than a
        # path. Iterating that would test its keys, which are not paths.
        if isinstance(value, dict):
            continue
        for path in [value] if isinstance(value, str) else value:
            assert path.startswith("./"), f"{key} path {path!r} must start with './'"


# --- skills and commands, as and when they exist ----------------------------

def test_every_skill_directory_holds_a_skill_document():
    for directory in sorted(p for p in (PLUGIN_ROOT / "skills").glob("*") if p.is_dir()):
        assert (directory / "SKILL.md").is_file(), f"{directory.name} has no SKILL.md"


def test_the_skill_collector_finds_every_skill_that_exists():
    # The parametrised checks below collect nothing when skill_files() returns an
    # empty list, and pytest reports that as skipped rather than failed. That is
    # correct while the plugin has no skills, and a false green the moment it does.
    # This ties the collector to what is actually on disk.
    directories = [p for p in (PLUGIN_ROOT / "skills").glob("*") if p.is_dir()]
    assert len(skill_files()) == len(directories), (
        f"{len(directories)} skill directories on disk but the collector found "
        f"{len(skill_files())}; the parametrised skill checks are not running"
    )


def test_the_command_collector_finds_every_command_that_exists():
    # Counted by walking the tree, deliberately not by reusing the collector's
    # own glob, so this cannot pass by comparing a function to itself. Commands
    # may be namespaced in subdirectories, so nested ones must be counted too.
    directory = PLUGIN_ROOT / "commands"
    on_disk = 0
    for _root, _dirs, files in os.walk(directory):
        on_disk += sum(1 for name in files if name.endswith(".md"))
    assert len(command_files()) == on_disk, (
        f"{on_disk} command documents on disk but the collector found "
        f"{len(command_files())}; the parametrised command checks are not running"
    )


@pytest.mark.parametrize("skill", skill_files(), ids=lambda p: p.parent.name)
def test_skill_frontmatter_names_match_their_directories(skill):
    meta, _ = read_frontmatter(skill)
    assert meta.get("name") == skill.parent.name
    assert is_kebab_case(skill.parent.name)


@pytest.mark.parametrize("command", command_files(), ids=lambda p: p.stem)
def test_command_filenames_are_kebab_case(command):
    assert is_kebab_case(command.stem)
