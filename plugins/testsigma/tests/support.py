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
ADAPTERS_DIR = PLUGIN_ROOT / "adapters"
REFERENCES_DIR = PLUGIN_ROOT / "references"

#: Where a Migration keeps its state, inside the source suite (ADR-0002).
MIGRATION_DIRECTORY = ".testsigma/migration/"

#: One file per concern, each readable and diffable on its own, because a person
#: reviews them and they land in the source repository's diffs.
MIGRATION_DIRECTORY_FILES = (
    "migration.md",
    "step-map.md",
    "open-questions.md",
    "platform-facts.md",
    "application-facts.md",
    "residue.md",
    "check-record.md",
)
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

#: The three properties every Source Adapter declares. They are independent —
#: every source shape met so far differs on them — so none may be omitted.
THREE_PROPERTIES = ("hides-sequence", "carries-locators", "value-language")

#: Section headings every adapter must carry. Presence is checked, never wording.
REQUIRED_ADAPTER_SECTIONS = (
    "Source Step",
    "Normalisation",
    "Sequence",
    "Locators",
    "Values",
    "Enumeration",
)

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


def adapter_files():
    """Every Source Adapter document, sorted. README.md is the format, not one."""
    if not ADAPTERS_DIR.is_dir():
        return []
    return sorted(
        path
        for path in ADAPTERS_DIR.glob("*.md")
        if path.name != "README.md"
    )


def markdown_sections(text):
    """Map each level-two heading to the text beneath it, up to the next one.

    Deeper headings stay inside their parent section, so a `###` subsection is
    part of the `##` section that contains it.
    """
    sections = {}
    heading = None
    buffer = []
    in_fence = False
    seen = []
    for line in text.splitlines():
        # A heading inside a fenced block is an example, not a heading. Without
        # this, a required section could be satisfied by a line of sample text.
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            if heading is not None:
                buffer.append(line)
            continue
        if not in_fence and line.startswith("## ") and not line.startswith("### "):
            if heading is not None:
                sections[heading] = "\n".join(buffer)
            heading = line[3:].strip()
            # A duplicate heading used to overwrite the first silently, so a
            # gutted section plus a verbatim copy further down passed every
            # check scoped to that heading. That is a worse false green than
            # the one section-scoping was introduced to fix.
            if heading in seen:
                raise ValueError(f"duplicate '## {heading}' heading")
            seen.append(heading)
            buffer = []
        elif heading is not None:
            buffer.append(line)
    if heading is not None:
        sections[heading] = "\n".join(buffer)
    return sections


def parse_count_table(text):
    """Read a two-column markdown table of `item` and count into a dict.

    Rows look like ``| `I am signed in` | 2 |``. The item must be in backticks,
    so a step containing a pipe cannot be mistaken for a column break, and the
    header and separator rows are skipped because neither parses as a count.
    """
    table = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 2:
            continue
        item, count = cells
        if not (item.startswith("`") and item.endswith("`")):
            continue
        try:
            table[item.strip("`")] = int(count)
        except ValueError:
            continue
    return table


def paragraphs(text):
    """Split text into blank-line-separated blocks.

    Used for co-occurrence assertions. Checking that two words appear somewhere
    in a long document proves almost nothing, because common words appear all
    over it. Checking that they appear in the same paragraph is a claim about a
    specific instruction rather than about vocabulary.

    Fenced blocks are atomic: a blank line inside one is part of the example.

    Known limit: a requirement written as bullets separated by blank lines is
    several paragraphs, so a co-occurrence assertion across them fails. That
    fails loudly rather than silently, so it is a nuisance and not a hazard —
    write the requirement as one block, or assert over a section instead.
    """
    blocks, current = [], []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            current.append(line)
            continue
        # A blank line inside a fenced block is part of the example, not a
        # paragraph break. Splitting there would hide a genuine instruction
        # from every co-occurrence assertion and fail loudly for no reason.
        if line.strip() or in_fence:
            current.append(line)
        elif current:
            blocks.append("\n".join(current))
            current = []
    if current:
        blocks.append("\n".join(current))
    return blocks


def has_paragraph_with(text, *terms, absent=()):
    """True when one paragraph holds every term and none of `absent`.

    Case-insensitive. `absent` exists because co-occurrence cannot read polarity:
    "do not refuse" contains "refuse", so an instruction can be inverted while
    keeping every word a test looks for. Naming the known inversions closes the
    cheap ones. It does not close the general case, and no string test will —
    that is what review is for.
    """
    wanted = [t.lower() for t in terms]
    forbidden = [t.lower() for t in absent]
    for block in paragraphs(text):
        # Whitespace-normalised, because a markdown line wrap is not semantic.
        # Without this a phrase straddling a wrap silently fails to match, and
        # the fix looks like reflowing prose to please a test.
        lowered = " ".join(block.split()).lower()
        if all(term in lowered for term in wanted) and not any(
            term in lowered for term in forbidden
        ):
            return True
    return False


def declared_files(reference_text):
    """The filenames a reference document declares, as `**`name.md`**` leads."""
    import re as _re

    return set(_re.findall(r"\*\*`([^`]+\.md)`\*\*", reference_text))
