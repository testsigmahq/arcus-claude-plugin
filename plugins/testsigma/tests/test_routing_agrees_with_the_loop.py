"""The layer that chooses a skill, held to ADR-0012.

A Migration run after the Phase framing was retired still defaulted to mapping
the whole vocabulary first. Every procedure was right: `map`'s own Step 0 works
across one scenario, and `convert` performs one Conversion and stops. The
default was decided before any of that prose was read.

A skill's `description` is a context pointer — loaded every turn, and its
wording rather than its target decides when the skill is reached. `map`
advertised "building or continuing the Step Map" and "working through unreviewed
rows", both of which are the suite-wide job, and `survey` ended by naming the
next step as mapping "in rows". Nothing tested either, because every other
document test in this suite reads section bodies.

So these read the routing layer: frontmatter descriptions, and the sentence a
stage hands over with.
"""

import pytest

from support import (
    SKILLS_DIR,
    document,
    has_paragraph_with,
    read_frontmatter,
    skill_files,
)


def _description(name):
    return _pointer(SKILLS_DIR / name / "SKILL.md")


def _pointer(path):
    """The skill's description — its always-loaded context pointer.

    `read_frontmatter` answers with a (frontmatter, body) pair, so the mapping
    is the first half of it.
    """
    frontmatter, _ = read_frontmatter(path)
    return frontmatter["description"]


def _body(name):
    return document(SKILLS_DIR / name / "SKILL.md").body


#: Wording that fires on a whole suite rather than on one Conversion. Mapping is
#: scoped by the scenario that reaches the steps (ADR-0012), so a pointer
#: offering the vocabulary entire is offering the retired shape.
BULK_TRIGGERS = (
    "building or continuing the step map",
    "working through unreviewed rows",
    "map the suite",
    "all unreviewed rows",
)


class TestNoPointerOffersTheSuiteEntire:
    @pytest.mark.parametrize(
        "path", skill_files(), ids=lambda p: p.parent.name
    )
    def test_a_description_fires_on_a_conversion_not_a_suite(self, path):
        description = _pointer(path).lower()
        for trigger in BULK_TRIGGERS:
            assert trigger not in description, (
                f"{path.parent.name} fires on the whole vocabulary: {trigger!r}"
            )


class TestMapSaysWhatScopesIt:
    def test_its_pointer_names_the_skill_that_calls_it(self):
        # `resolve-elements` states the same relationship and is reached
        # correctly. `map` never said it, so nothing stopped a session from
        # treating it as the next stage of the Migration.
        assert "called by convert" in _description("map").lower()

    def test_its_pointer_says_what_bounds_the_work(self):
        assert "one scenario" in _description("map").lower()

    def test_its_gate_requires_a_conversion_and_not_only_a_migration(self):
        # A Migration Directory is what mapping writes into. A Conversion is
        # what decides which rows are in scope at all.
        assert has_paragraph_with(_body("map"), "Conversion", "scenario")


class TestSurveyHandsOverToTheFirstConversion:
    def test_it_names_the_conversion_as_what_happens_next(self):
        assert has_paragraph_with(_body("survey"), "what happens next", "Conversion")

    def test_it_sizes_the_next_step_in_scenarios(self):
        # "how large it is in rows" is the vocabulary, which is the unit of the
        # job this loop replaced.
        assert "in rows rather than in hours" not in _body("survey")
