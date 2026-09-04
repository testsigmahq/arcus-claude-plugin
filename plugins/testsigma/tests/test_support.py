"""Tests for the shared document helpers every later ticket depends on."""

import pytest

from support import (
    ADR_DIR,
    MANIFEST,
    PLUGIN_ROOT,
    REPO_ROOT,
    FrontmatterError,
    git_ignores,
    is_kebab_case,
    has_paragraph_with,
    markdown_sections,
    paragraphs,
    parse_count_table,
    split_frontmatter,
)


# --- split_frontmatter -------------------------------------------------------

def test_splits_frontmatter_from_body():
    meta, body = split_frontmatter("---\nname: mapping\n---\nDo the thing.\n")
    assert meta == {"name": "mapping"}
    assert body.strip() == "Do the thing."


def test_parses_a_list_value():
    meta, _ = split_frontmatter("---\ntags:\n  - one\n  - two\n---\nbody\n")
    assert meta["tags"] == ["one", "two"]


def test_parses_an_inline_list_value():
    meta, _ = split_frontmatter('---\ntags: ["one", "two"]\n---\nbody\n')
    assert meta["tags"] == ["one", "two"]


def test_a_document_with_no_frontmatter_is_an_error():
    with pytest.raises(FrontmatterError):
        split_frontmatter("# Just a heading\n")


def test_an_unterminated_frontmatter_block_is_an_error():
    with pytest.raises(FrontmatterError):
        split_frontmatter("---\nname: mapping\nnever closed\n")


def test_malformed_yaml_is_reported_as_a_frontmatter_error():
    # Callers should never have to catch a yaml-specific exception.
    with pytest.raises(FrontmatterError):
        split_frontmatter("---\n\tbad: [unclosed\n---\nbody\n")


def test_frontmatter_that_is_not_a_mapping_is_an_error():
    with pytest.raises(FrontmatterError):
        split_frontmatter("---\n- a list, not a mapping\n---\nbody\n")


def test_an_indented_fence_inside_a_block_scalar_does_not_close_frontmatter():
    # A long skill description is a YAML block scalar, and an indented `---`
    # inside one is ordinary text. Closing the block there drops every key
    # below it into the body without raising, which is silent data loss.
    meta, body = split_frontmatter(
        "---\n"
        "name: my-skill\n"
        "description: |\n"
        "  Use this when the user says:\n"
        "  ---\n"
        "  and then continues.\n"
        "allowed-tools: Read\n"
        "---\n"
        "Real body.\n"
    )
    assert meta["name"] == "my-skill"
    assert meta["allowed-tools"] == "Read", "a key below the indented fence was lost"
    assert "and then continues." in meta["description"]
    assert body.strip() == "Real body."


def test_an_indented_opening_fence_is_not_frontmatter():
    with pytest.raises(FrontmatterError):
        split_frontmatter("   ---\nname: x\n---\nbody\n")


def test_body_is_returned_even_when_it_contains_a_triple_dash():
    meta, body = split_frontmatter("---\nname: x\n---\nbefore\n---\nafter\n")
    assert meta == {"name": "x"}
    assert "before" in body and "after" in body


# --- is_kebab_case -----------------------------------------------------------

@pytest.mark.parametrize("name", ["map", "write-an-adapter", "resolve-elements"])
def test_accepts_kebab_case(name):
    assert is_kebab_case(name)


@pytest.mark.parametrize(
    "name", ["Map", "writeAnAdapter", "write_an_adapter", "-leading", "trailing-", "a--b", ""]
)
def test_rejects_everything_else(name):
    assert not is_kebab_case(name)


def test_rejects_a_non_string_without_raising():
    # A manifest with a numeric name should fail as "not kebab-case", not
    # explode with a TypeError from inside the matcher.
    assert not is_kebab_case(5)
    assert not is_kebab_case(None)


# --- git_ignores -------------------------------------------------------------

def test_git_ignores_is_false_for_a_file_that_is_plainly_visible():
    assert not git_ignores(MANIFEST)


def test_git_ignores_refuses_a_path_that_does_not_exist():
    # check-ignore exits 1 both for "not ignored" and for "no such file", so
    # without this a deleted file reads as visible.
    with pytest.raises(FileNotFoundError):
        git_ignores(PLUGIN_ROOT / "does-not-exist.md")


# --- markdown_sections -------------------------------------------------------

def test_maps_level_two_headings_to_their_bodies():
    sections = markdown_sections("# Title\n\n## One\nalpha\n\n## Two\nbeta\n")
    assert sections["One"].strip() == "alpha"
    assert sections["Two"].strip() == "beta"


def test_a_deeper_heading_stays_inside_its_parent_section():
    sections = markdown_sections("## One\nalpha\n### Sub\nnested\n## Two\nbeta\n")
    assert "nested" in sections["One"]
    assert "Sub" not in sections


def test_a_heading_inside_a_fenced_block_is_not_a_section():
    # Otherwise a required-section check could be satisfied by sample text.
    sections = markdown_sections(
        "## One\nalpha\n```markdown\n## Example only\n```\nstill one\n\n## Two\nbeta\n"
    )
    assert sorted(sections) == ["One", "Two"]
    assert "still one" in sections["One"]


def test_a_fenced_block_is_kept_in_its_section_body():
    sections = markdown_sections("## One\n```\ncode\n```\n")
    assert "code" in sections["One"]


def test_text_before_the_first_heading_is_not_a_section():
    assert markdown_sections("preamble\n\n## One\nalpha\n") == {"One": "alpha"}


# --- parse_count_table -------------------------------------------------------

def test_reads_a_two_column_count_table():
    text = "| Source Step | Occurrences |\n|---|---|\n| `a step` | 4 |\n| `another` | 1 |\n"
    assert parse_count_table(text) == {"a step": 4, "another": 1}


def test_skips_rows_whose_item_is_not_in_backticks():
    assert parse_count_table("| plain | 3 |\n| `ok` | 1 |\n") == {"ok": 1}


def test_skips_rows_whose_count_is_not_a_number():
    assert parse_count_table("| `a` | many |\n| `b` | 2 |\n") == {"b": 2}


def test_a_step_containing_a_pipe_is_not_split():
    # Backticks are required precisely so this cannot happen silently.
    assert parse_count_table("| `a | b` | 2 |\n") == {}


# --- paragraphs / has_paragraph_with -----------------------------------------

def test_splits_on_blank_lines():
    assert paragraphs("one\ntwo\n\nthree\n") == ["one\ntwo", "three"]


def test_a_blank_line_inside_a_fenced_block_does_not_split_it():
    # Otherwise a genuine instruction inside an example becomes invisible to
    # every co-occurrence assertion, failing loudly for no reason.
    doc = "```bash\ngit rev-parse\n\necho refuse\n```\n"
    assert len(paragraphs(doc)) == 1
    assert has_paragraph_with(doc, "rev-parse", "refuse")


def test_co_occurrence_is_within_one_paragraph_not_the_whole_text():
    doc = "names version control here\n\nand refuses somewhere else\n"
    assert not has_paragraph_with(doc, "version control", "refuse")
    assert has_paragraph_with("version control, and refuse\n", "version control", "refuse")


def test_co_occurrence_ignores_case():
    assert has_paragraph_with("Version Control and REFUSE\n", "version control", "refuse")


# --- path constants ----------------------------------------------------------

def test_paths_point_where_they_claim():
    assert (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").is_file()
    assert (REPO_ROOT / ".claude-plugin" / "marketplace.json").is_file()
    assert ADR_DIR.is_dir()

class TestParseCountTableHandlesAPipeInACell:
    """A real Tosca module is named `M&T Org Search | CHIP`.

    The helper's docstring used to claim backticks protected such a cell from
    being read as a column break. They do not: the row parsed as three cells and
    was dropped from the table silently, so the counts were short by that row
    with nothing said.
    """

    TABLE = (
        "| Source Step | Occurrences |\n"
        "|---|---|\n"
        "| `M&T Inventory` | 4 |\n"
        "| `M&T Org Search \\| CHIP` | 2 |\n"
    )

    def test_an_escaped_pipe_keeps_the_row(self):
        table = parse_count_table(self.TABLE)
        assert table == {"M&T Inventory": 4, "M&T Org Search | CHIP": 2}

    def test_the_pipe_survives_in_the_parsed_name(self):
        assert "M&T Org Search | CHIP" in parse_count_table(self.TABLE)

    def test_an_unescaped_pipe_still_drops_the_row_rather_than_guessing(self):
        # Loud by absence is not ideal, but splitting a cell in two and
        # inventing a count would be worse. The adapter contract's
        # worked-example test is what notices a short table.
        table = parse_count_table(
            "| `M&T Inventory` | 4 |\n| `M&T Org Search | CHIP` | 2 |\n"
        )
        assert table == {"M&T Inventory": 4}
