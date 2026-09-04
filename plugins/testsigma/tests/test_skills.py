"""The contract every skill document must satisfy, plus the survey skill.

Structural and topic-presence only. Where a test insists on a word it is because
the ticket requires that instruction to exist, never because of how it reads.
"""

import pytest

from support import (
    MIGRATION_DIRECTORY,
    MIGRATION_DIRECTORY_FILES,
    PLUGIN_ROOT,
    declared_files,
    REFERENCES_DIR,
    has_paragraph_with,
    is_kebab_case,
    paragraphs,
    markdown_sections,
    read_frontmatter,
    skill_files,
)

SURVEY = PLUGIN_ROOT / "skills" / "survey" / "SKILL.md"


def _body(path):
    _, body = read_frontmatter(path)
    return body


def _lower(path):
    return _body(path).lower()


# --- every skill -------------------------------------------------------------

def test_there_is_at_least_one_skill():
    assert skill_files(), "no skills found; the checks below would prove nothing"


@pytest.mark.parametrize("skill", skill_files(), ids=lambda p: p.parent.name)
class TestEverySkill:
    def test_name_matches_its_directory(self, skill):
        meta, _ = read_frontmatter(skill)
        assert meta.get("name") == skill.parent.name
        assert is_kebab_case(skill.parent.name)

    def test_has_a_description(self, skill):
        meta, _ = read_frontmatter(skill)
        description = str(meta.get("description", "")).strip()
        # The description is what a request is matched against, so a stub is a
        # skill that never triggers.
        assert len(description) > 40, "description is too short to match a request against"

    def test_body_opens_with_a_title(self, skill):
        assert _body(skill).lstrip().startswith("# "), "skill body has no title"

    def test_body_stays_within_the_progressive_disclosure_budget(self, skill):
        # A skill body loads whole when the skill triggers. Detail belongs in a
        # reference document that is read only when needed.
        words = len(_body(skill).split())
        # A discipline threshold, not a runaway guard. At 5000 the advice to
        # move detail into a reference arrives far too late to act on.
        assert words < 2500, f"skill body is {words} words; move detail into references/"

    def test_a_skill_touching_the_migration_directory_points_at_its_definition(self, skill):
        body = _body(skill)
        # Triggered on the prose name as well as the literal path. A skill that
        # writes to the directory but only ever calls it by name used to skip,
        # and a skip is indistinguishable from "not applicable".
        touches = MIGRATION_DIRECTORY in body or "migration directory" in body.lower()
        if not touches:
            pytest.skip("this skill does not touch the Migration Directory")
        assert "references/migration-directory.md" in body, (
            "the Migration Directory's file set is defined in one place; a skill "
            "that writes to it must point at that definition rather than restate it"
        )


# --- the shared reference ----------------------------------------------------

def test_the_cli_probe_procedure_is_defined_in_one_place():
    reference = REFERENCES_DIR / "cli-probe.md"
    assert reference.is_file(), "ADR-0003 states the policy; somewhere must state the method"
    body = reference.read_text(encoding="utf-8").lower()
    # The two failure modes it exists to prevent.
    assert "not covered" in body, "an absent check must be recorded as not covered"
    assert "attach" in body and "sprints" in body, (
        "it must say how to tell the two programs called testsigma apart"
    )


def test_every_migration_directory_file_has_a_skeleton():
    body = (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")
    for filename in MIGRATION_DIRECTORY_FILES:
        stem = filename.replace(".md", "")
        heading = "# " + stem.replace("-", " ")
        assert f"`{filename}`:" in body or heading.lower() in body.lower(), (
            f"{filename} has no skeleton, so each skill will invent a different one"
        )


def test_the_residue_table_is_keyed_by_step_and_element():
    # The two Residue causes do not share a granularity: an unexpressible step
    # blocks a whole row, an unresolved element blocks only the occurrences
    # naming it. A table keyed by Source Step alone cannot say which.
    body = (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")
    header = next(
        line for line in body.splitlines()
        if line.startswith("| Source Step |") and "Cause" in line
    )
    assert "Element" in header, f"residue.md cannot key an element: {header}"


def test_the_migration_directory_is_defined_in_one_place():
    reference = REFERENCES_DIR / "migration-directory.md"
    assert reference.is_file(), "the Migration Directory needs a single definition"
    # Set equality, so drift fails in both directions: a file named in the
    # reference but not declared here, and one declared here but undescribed.
    assert declared_files(reference.read_text(encoding="utf-8")) == set(
        MIGRATION_DIRECTORY_FILES
    )


# --- the survey skill --------------------------------------------------------

class TestSurveySkill:
    def test_it_exists(self):
        assert SURVEY.is_file()

    def test_its_description_says_it_starts_a_migration(self):
        meta, _ = read_frontmatter(SURVEY)
        description = str(meta.get("description", "")).lower()
        assert "migration" in description
        assert "start" in description or "begin" in description

    # The three gates are asserted inside the refusals section rather than
    # anywhere in the document. Both scopings matter. A word present somewhere
    # proves nothing, because these words recur throughout the skill; and a gate
    # that has drifted out of the section that says "check all three before
    # doing any work" is no longer a gate.
    def _refusals(self):
        # markdown_sections raises on a duplicate heading, which is what stops a
        # gutted section plus a verbatim copy lower down from satisfying these.
        sections = markdown_sections(_body(SURVEY))
        headings = list(sections)
        matching = [h for h in headings if "refusal" in h.lower()]
        assert len(matching) == 1, (
            f"expected exactly one section whose heading names the refusals, found "
            f"{len(matching)}. If the heading was renamed, these gate tests need "
            f"updating together. Headings are: {headings}"
        )
        # A gate that has drifted below the steps is no longer a gate.
        first_step = next(
            (i for i, h in enumerate(headings) if h.lower().startswith("step 1")), len(headings)
        )
        assert headings.index(matching[0]) < first_step, (
            "the refusals must come before the first step, not after it"
        )
        return sections[matching[0]]

    def test_it_refuses_a_source_without_version_control(self):
        # This refusal exists because it has already gone wrong: the conversion
        # that produced this plugin's design sat unversioned in a temporary
        # directory holding the only copy of everything it had made.
        assert has_paragraph_with(
            self._refusals(),
            "version control",
            "refuse",
            absent=("do not refuse", "proceed anyway", "nice-to-have"),
        ), "the refusals section does not refuse a source without version control"

    def test_it_probes_the_installed_cli_before_starting(self):
        assert has_paragraph_with(self._refusals(), "testsigma --version", "stop"), (
            "the refusals section does not stop when the CLI is absent"
        )

    def test_it_records_which_checks_the_installed_build_performs(self):
        body = _body(SURVEY)
        assert has_paragraph_with(body, "record", "build"), "the CLI build is not recorded"
        assert has_paragraph_with(body, "not covered", "assume"), (
            "the skill must say an unavailable check is recorded as not covered "
            "rather than assumed to pass"
        )

    def test_it_names_the_adapter_and_why_before_other_work(self):
        assert has_paragraph_with(
            _body(SURVEY), "adapter", "why", "before"
        ), "the adapter choice must be stated, with its reason, before other work"

    def test_it_reports_the_collapse_ratio_and_warns_when_it_is_near_one(self):
        assert has_paragraph_with(
            _body(SURVEY), "collapse ratio", "1.0"
        ), "the near-1.0 warning must be attached to the Collapse Ratio, not merely present"

    def test_it_creates_the_migration_directory_inside_the_source(self):
        assert MIGRATION_DIRECTORY in _body(SURVEY)

    def test_it_refuses_to_start_over_an_existing_migration(self):
        assert has_paragraph_with(
            self._refusals(),
            MIGRATION_DIRECTORY,
            "already",
            absent=("proceed anyway", "overwrite it if", "clean slate"),
        ), "the refusals section does not refuse a Migration that has already started"

    def test_each_gate_is_its_own_instruction(self):
        # Shape, not content: the three gate tests above verify the instructions
        # exist. This only stops two gates being merged into one run-on
        # paragraph, which would keep both phrase-pairs co-occurring while
        # losing the "check all three" structure. A thin backstop, and said to
        # be one rather than dressed up as a gate.
        assert len(paragraphs(self._refusals())) >= 4

    def test_it_establishes_which_folder_is_the_suite_before_checking_anything(self):
        # Everything else is relative to this, and a suite is often a
        # subdirectory of the repository that holds it.
        sections = list(markdown_sections(_body(SURVEY)))
        assert any("folder is the source suite" in h.lower() for h in sections), (
            "the skill never establishes which folder the suite is"
        )
        first_refusal = next(i for i, h in enumerate(sections) if "refusal" in h.lower())
        establishes = next(i for i, h in enumerate(sections) if "source suite" in h.lower())
        assert establishes < first_refusal, "the suite root must be settled before the gates"

    def test_it_checks_the_migration_directory_is_not_ignored(self):
        # A repository that ignores dot directories makes every commit of the
        # Migration's state silently do nothing. That is the failure version
        # control was required to prevent, arriving quietly.
        assert has_paragraph_with(_body(SURVEY), "check-ignore", "stop")

    def test_it_notices_a_submodule_without_refusing_one(self):
        assert has_paragraph_with(_body(SURVEY), "submodule", "confirm")

    def test_it_records_the_branch_and_handles_a_detached_head(self):
        assert has_paragraph_with(_body(SURVEY), "branch", "detached head")

    def test_it_gives_a_threshold_for_the_near_one_warning(self):
        # "Near 1.0" with no number fires on whim.
        assert has_paragraph_with(_body(SURVEY), "collapse ratio", "1.0", "1.5")

    def test_it_refuses_to_choose_quietly_between_two_adapters(self):
        assert has_paragraph_with(_body(SURVEY), "two adapters", "operator")

    def test_the_directory_pointer_sits_where_the_directory_is_created(self):
        # A mention anywhere in the document is the whole-body vocabulary
        # failure this suite exists to avoid.
        sections = markdown_sections(_body(SURVEY))
        creating = [v for k, v in sections.items() if "create the migration directory" in k.lower()]
        assert len(creating) == 1
        assert "references/migration-directory.md" in creating[0], (
            "the step that creates the directory must point at its definition"
        )

    def test_it_points_at_the_cli_probe_procedure(self):
        assert "references/cli-probe.md" in _body(SURVEY), (
            "Step 3 states a policy; the procedure lives in a reference"
        )

    def test_it_scopes_the_commit(self):
        # A bare commit of everything sweeps unrelated work in a monorepo.
        assert has_paragraph_with(_body(SURVEY), "git add .testsigma/migration", "never")

    def test_it_names_the_audience_rule(self):
        assert has_paragraph_with(_body(SURVEY), "operator", "context.md")

    def test_the_directory_is_created_before_the_expensive_step(self):
        # Enumeration is the long step. Everything before it is a cheap fact
        # that would be lost with the session, and the ratio question needs
        # open-questions.md to already exist.
        sections = list(markdown_sections(_body(SURVEY)))
        create = next(i for i, h in enumerate(sections) if "create the migration directory" in h.lower())
        enumerate_ = next(i for i, h in enumerate(sections) if "enumerate" in h.lower())
        assert create < enumerate_, (
            "the Migration Directory must exist and be committed before enumeration"
        )

    def test_it_allows_scripting_the_mechanical_rule_but_not_the_judgement(self):
        assert has_paragraph_with(_body(SURVEY), "script", "judgement")

    def test_it_has_the_steps_a_reader_needs(self):
        sections = markdown_sections(_body(SURVEY))
        assert len(sections) >= 4, f"survey has only {len(sections)} sections"
