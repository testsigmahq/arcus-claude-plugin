"""Shared helpers for the testsigma plugin's document contract tests.

The plugin is made entirely of markdown, so "the code under test" is a set of
documents. These helpers locate them and read their frontmatter. Every later
ticket's tests build on this module.
"""

import re
import subprocess
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]

MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CONTEXT = PLUGIN_ROOT / "CONTEXT.md"
ADR_DIR = PLUGIN_ROOT / "docs" / "adr"
SKILLS_DIR = PLUGIN_ROOT / "skills"
COMMANDS_DIR = PLUGIN_ROOT / "commands"

_KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_FENCE = "---"


class FrontmatterError(ValueError):
    """A document's frontmatter is absent, unterminated, or not a mapping.

    Callers get this for every frontmatter problem, so no test has to catch a
    yaml-specific exception.
    """


def split_frontmatter(text):
    """Return (metadata dict, body string) for a document with frontmatter.

    Raises FrontmatterError when the document has no frontmatter block, when the
    block is never closed, when it is not valid YAML, or when it parses to
    anything other than a mapping.
    """
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != _FENCE:
        raise FrontmatterError("document does not open with a '---' frontmatter fence")

    for index in range(1, len(lines)):
        if lines[index].rstrip() == _FENCE:
            raw = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :])
            break
    else:
        raise FrontmatterError("frontmatter block is never closed")

    try:
        meta = yaml.safe_load(raw) if raw.strip() else {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"frontmatter is not valid YAML: {exc}") from exc

    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise FrontmatterError(f"frontmatter must be a mapping, got {type(meta).__name__}")
    return meta, body


def read_frontmatter(path):
    """split_frontmatter for a file, naming the file in any error raised."""
    try:
        return split_frontmatter(Path(path).read_text(encoding="utf-8"))
    except FrontmatterError as exc:
        raise FrontmatterError(f"{path}: {exc}") from exc


def is_kebab_case(name):
    """True when name is lowercase words joined by single hyphens."""
    return isinstance(name, str) and bool(_KEBAB.match(name))


def git_ignores(path):
    """True when git would ignore path.

    This is the check that matters for the plugin's own docs. Whether a file is
    committed yet moves constantly during development; whether an ignore rule
    hides it is a standing property, and hiding them is the fault that actually
    occurred.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist, so asking whether git ignores it proves nothing"
        )
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"git check-ignore failed for {path}: {result.stderr.decode(errors='replace')}"
        )
    return result.returncode == 0


def is_git_repo():
    """True when the plugin sits inside a git working tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(REPO_ROOT),
            capture_output=True,
        )
    except (OSError, FileNotFoundError):
        return False
    return result.returncode == 0 and result.stdout.strip() == b"true"


def git_tracked_paths(directory):
    """Paths git actually tracks under directory, relative to the repo root.

    Complements git_ignores. Not being ignored is a standing property; being
    present in the repository is a different one, and a file that was committed
    and later deleted fails only this check.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", str(directory)],
            cwd=str(REPO_ROOT),
            capture_output=True,
        )
    except (OSError, FileNotFoundError):
        return set()
    if result.returncode != 0:
        return set()
    return {
        REPO_ROOT / entry
        for entry in result.stdout.decode(errors="replace").split("\0")
        if entry
    }


def adr_files():
    """Every ADR in the plugin, sorted by filename."""
    return sorted(ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")) if ADR_DIR.is_dir() else []


def skill_files():
    """Every SKILL.md in the plugin, sorted by path."""
    return sorted(SKILLS_DIR.glob("*/SKILL.md")) if SKILLS_DIR.is_dir() else []


def command_files():
    """Every command document in the plugin, sorted by path."""
    return sorted(COMMANDS_DIR.rglob("*.md")) if COMMANDS_DIR.is_dir() else []
