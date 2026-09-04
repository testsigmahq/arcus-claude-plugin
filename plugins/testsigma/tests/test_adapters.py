"""The contract every Source Adapter document must satisfy.

Structural only. These check that a required declaration or section is present,
never how its prose reads, so rewording an adapter is free.

One deliberate exception: where a source hides its sequence behind a helper
layer, the Sequence section is required to mention both sequence and locators.
That is topic presence rather than phrasing — every sentence around those two
words can change freely — but it is the one place the suite insists on a word.
"""

import pytest

from support import (
    ADAPTERS_DIR,
    REQUIRED_ADAPTER_SECTIONS,
    THREE_PROPERTIES,
    adapter_files,
    is_kebab_case,
    markdown_sections,
    read_frontmatter,
)

VALID_PROPERTY_VALUES = {"yes", "no", "sometimes"}


def test_the_adapters_directory_exists():
    assert ADAPTERS_DIR.is_dir(), "adapters live at the plugin root, beside skills"


def test_there_is_at_least_one_adapter():
    # Without this every parametrised check below would pass vacuously.
    assert adapter_files(), "no adapters found; the checks below would prove nothing"


def test_the_adapter_collector_finds_every_adapter_that_exists():
    # Counted by walking, deliberately not by reusing the collector's own glob,
    # so this cannot pass by comparing a function to its own implementation.
    on_disk = [
        path
        for path in ADAPTERS_DIR.iterdir()
        if path.is_file() and path.suffix == ".md" and path.name != "README.md"
    ]
    assert len(adapter_files()) == len(on_disk), (
        f"{len(on_disk)} adapters on disk but the collector found "
        f"{len(adapter_files())}; the parametrised checks are not running"
    )


def test_the_format_is_documented():
    readme = ADAPTERS_DIR / "README.md"
    assert readme.is_file(), "the adapter format itself must be written down"
    sections = markdown_sections(readme.read_text(encoding="utf-8"))
    assert "Frontmatter" in sections
    assert "Required sections" in sections


@pytest.mark.parametrize("adapter", adapter_files(), ids=lambda p: p.stem)
class TestEveryAdapter:
    def test_name_matches_its_filename(self, adapter):
        meta, _ = read_frontmatter(adapter)
        assert meta.get("name") == adapter.stem
        assert is_kebab_case(adapter.stem)

    def test_describes_its_source_format(self, adapter):
        meta, _ = read_frontmatter(adapter)
        assert str(meta.get("source", "")).strip(), "adapter does not say what it reads"

    @pytest.mark.parametrize("prop", THREE_PROPERTIES)
    def test_declares_each_of_the_three_properties(self, adapter, prop):
        meta, _ = read_frontmatter(adapter)
        assert prop in meta, (
            f"{adapter.name} does not declare {prop!r}; all three properties are "
            "required because none can be inferred from the others"
        )

    @pytest.mark.parametrize("prop", THREE_PROPERTIES)
    def test_each_property_has_a_value_from_the_fixed_set(self, adapter, prop):
        meta, _ = read_frontmatter(adapter)
        value = meta.get(prop)
        # yes/no unquoted are YAML booleans; accept them, coerced, rather than
        # failing on a quoting detail.
        if isinstance(value, bool):
            value = "yes" if value else "no"
        assert value in VALID_PROPERTY_VALUES, (
            f"{adapter.name} declares {prop} as {meta.get(prop)!r}; "
            f"expected one of {sorted(VALID_PROPERTY_VALUES)}"
        )

    @pytest.mark.parametrize("section", REQUIRED_ADAPTER_SECTIONS)
    def test_carries_every_required_section(self, adapter, section):
        _, body = read_frontmatter(adapter)
        assert section in markdown_sections(body), (
            f"{adapter.name} has no '## {section}' section"
        )

    def test_a_source_that_hides_sequence_says_to_read_it_for_sequence(self, adapter):
        # Topic presence, not phrasing: where a helper layer hides the sequence,
        # the Sequence section has to address both sequence and locators,
        # because reading those files for locators alone is the fault that
        # produced four of the six known faults.
        meta, body = read_frontmatter(adapter)
        hides = meta.get("hides-sequence")
        if isinstance(hides, bool):
            hides = "yes" if hides else "no"
        if hides == "no":
            pytest.skip("this source hides nothing, so there is nothing to insist on")
        section = markdown_sections(body).get("Sequence", "").lower()
        assert "sequence" in section, "the Sequence section must discuss sequence"
        assert "locator" in section, (
            "an adapter whose source hides sequence must say that the helper is "
            "opened for sequence and not only for locators"
        )

    def test_the_enumeration_section_ends_in_a_worked_example(self, adapter):
        from support import parse_count_table

        _, body = read_frontmatter(adapter)
        section = markdown_sections(body).get("Enumeration", "")
        table = parse_count_table(section)
        assert table, (
            f"{adapter.name} has no worked example in its Enumeration section; "
            "the format requires a table of Source Steps with occurrence counts"
        )
        assert all(count >= 1 for count in table.values())
