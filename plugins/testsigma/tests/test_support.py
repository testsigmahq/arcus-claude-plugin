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
    document,
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


# --- document ----------------------------------------------------------------
#
# Eight modules each rebuilt `_section` over `markdown_sections`, and two copies
# of its failure message had already drifted apart. None of the eight was
# tested: the helper that decides whether a whole file's assertions target the
# right text had no test of its own anywhere in the suite.

def _written(tmp_path, text):
    path = tmp_path / "doc.md"
    path.write_text(text, encoding="utf-8")
    return path


BODY = """---
name: sample
---

# Title

## Opening the helper

Read it for sequence.

## Closing

Done.
"""


def test_a_handle_exposes_the_body_without_its_frontmatter(tmp_path):
    doc = document(_written(tmp_path, BODY))
    assert doc.body.lstrip().startswith("# Title")
    assert "name: sample" not in doc.body


def test_a_handle_reads_the_frontmatter_too(tmp_path):
    assert document(_written(tmp_path, BODY)).meta["name"] == "sample"


def test_a_handle_finds_a_section_by_part_of_its_heading(tmp_path):
    doc = document(_written(tmp_path, BODY))
    assert "sequence" in doc.section("helper")


def test_a_needle_matching_no_section_names_the_headings_that_exist(tmp_path):
    # The diagnosable failure: a renamed section is the commonest cause, and
    # the message has to say what the document actually holds.
    doc = document(_written(tmp_path, BODY))
    with pytest.raises(AssertionError) as raised:
        doc.section("residue")
    message = str(raised.value)
    assert "residue" in message
    assert "Opening the helper" in message and "Closing" in message


def test_a_needle_matching_two_sections_refuses_rather_than_choosing(tmp_path):
    # Picking the first would let a document satisfy an assertion twice over,
    # from either of two sections, with no way to tell which.
    doc = document(_written(tmp_path, BODY.replace("## Closing", "## Closing the helper")))
    with pytest.raises(AssertionError) as raised:
        doc.section("helper")
    assert "2" in str(raised.value)


def test_a_duplicate_heading_is_still_refused_through_the_handle(tmp_path):
    # markdown_sections raises on one deliberately: a gutted section plus a
    # verbatim copy lower down would otherwise satisfy everything asserted
    # against either. The handle must not soften that.
    doc = document(_written(tmp_path, BODY + "\n## Closing\n\nAgain.\n"))
    with pytest.raises(Exception):
        doc.sections


def test_a_handle_flattens_whitespace_on_request(tmp_path):
    # A markdown line wrap is not semantic, and three phrase-ownership controls
    # in this suite were silently vacuous until they normalised.
    doc = document(_written(tmp_path, "---\nname: x\n---\n\n# T\n\nRead it\nfor sequence.\n"))
    assert "read it for sequence." in doc.flat


def test_a_handle_works_on_a_document_with_no_frontmatter(tmp_path):
    # References and ADRs carry none; only skills and commands do.
    doc = document(_written(tmp_path, "# Plain\n\n## One\n\nText.\n"))
    assert doc.meta == {}
    assert "Text." in doc.section("one")


def test_malformed_frontmatter_raises_rather_than_reading_as_absent(tmp_path):
    # The distinction the handle first got wrong: a document that *claims*
    # frontmatter and cannot be parsed is broken, and must say so. Swallowing
    # it made a skill with a bad opening block read as one with no frontmatter,
    # so a test asserting on `name` reported a missing field — or passed
    # vacuously — instead of naming the parse error.
    path = _written(tmp_path, "---\nname: [unclosed\n---\n\n# T\n")
    with pytest.raises(FrontmatterError):
        document(path).meta
    with pytest.raises(FrontmatterError):
        document(path).body


def test_unterminated_frontmatter_raises_too(tmp_path):
    path = _written(tmp_path, "---\nname: sample\n\n# T\n\nNo closing fence.\n")
    with pytest.raises(FrontmatterError):
        document(path).meta


def test_a_document_that_claims_no_frontmatter_is_not_a_parse_error(tmp_path):
    # The other half: a reference opens with `# Title` and carries none, and
    # that is not a fault.
    doc = document(_written(tmp_path, "# Plain\n\nText.\n"))
    assert doc.meta == {}
    assert doc.body.startswith("# Plain")
