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

#: Permission-granting vocabulary. In a document whose sections state absolute
#: rules, none of these belongs, and a rule is most often gutted by adding a
#: paragraph that grants permission rather than by editing the rule itself.
PERMISSIVE_HEDGES = (
    "it is fine to",
    "it's fine to",
    "reasonable to",
    "acceptable to",
    "is acceptable",
    "a nicety",
    "rather than a requirement",
    "rather than a rule",
    "no need to",
    "is optional",
    "if you prefer",
    "at your discretion",
    "feel free",
    "should simply be shown",
    "use your judgement",
    "in practice either",
    "walk it back",
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


def preamble(text):
    """The text before the first level-two heading.

    markdown_sections only starts buffering once it has seen a heading, so
    everything above the first `##` is invisible to every section-scoped
    assertion. A review put a carve-out there — a stale tenant result being
    logged against a later session — that gutted two load-bearing rules while
    the whole suite stayed green. This is what lets the preamble be checked too.

    Fence-aware, so a `##` inside an example does not end the preamble.
    """
    lines = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        if not in_fence and line.startswith("## "):
            break
        lines.append(line)
    return "\n".join(lines)


#: Stands in for an escaped pipe while a table row is split on unescaped ones.
_ESCAPED_PIPE = "\x00pipe\x00"


def parse_count_table(text):
    """Read a two-column markdown table of `item` and count into a dict.

    Rows look like ``| `I am signed in` | 2 |``.

    An escaped pipe inside a cell is honoured. Backticks do not protect one:
    this used to claim they did, and a real Tosca module named
    ``M&T Org Search | CHIP`` produced three cells and was dropped from the
    parsed table without a word — the row was simply absent from the counts.
    A silently short table is worse than a parse error, so the escape is
    handled and an unescaped pipe still fails the row loudly by cell count.
    """
    table = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        line = line.replace("\\|", _ESCAPED_PIPE)
        cells = [
            cell.strip().replace(_ESCAPED_PIPE, "|")
            for cell in line.strip("|").split("|")
        ]
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


def hedges_in(text):
    """Permission-granting phrases found anywhere in text.

    Section-wide rather than paragraph-scoped, and that is the point. Every
    other assertion here is a positive existence check, so a rule can be gutted
    by keeping its sentence intact and adding a second paragraph beside it that
    grants an exception. A review demonstrated four of those at once, all
    passing. Paragraph scoping cannot see them, because the correct paragraph is
    still there.

    This narrows the class rather than closing it, and the residual gap has been
    demonstrated rather than merely predicted: a review wrote a walk-back in
    neutral procedural language — a row proceeding with its comparison "noted as
    pending" rather than blocking — and the suite stayed green. Granting
    permission is hard to write without permissive words, which is what makes
    this worth having, but "does this document contradict itself" is not
    decidable by string matching and no addition to this list makes it so.

    Do not extend this list to chase a specific demonstrated bypass. Two controls
    cover the general case: review, which is what found the one above, and the
    behavioural evals of ticket 13, which are the higher seam because they test
    what an agent does rather than what a document says.

    Applied to whole sections and, via `preamble`, to the text above the first
    heading, which was invisible to every assertion until a review hid a
    carve-out there. Not applied to whole documents: that version failed the
    survey skill on "a guideline rather than a rule", which is a deliberate
    design decision about a threshold. The scanner cannot tell an intended
    guideline from a walk-back, so applied everywhere it would pressure honest
    prose rather than catch anything.
    """
    flattened = " ".join(text.split()).lower()
    return sorted({hedge for hedge in PERMISSIVE_HEDGES if hedge in flattened})


def declared_files(reference_text):
    """The filenames a reference document declares, as `**`name.md`**` leads."""
    import re as _re

    return set(_re.findall(r"\*\*`([^`]+\.md)`\*\*", reference_text))
