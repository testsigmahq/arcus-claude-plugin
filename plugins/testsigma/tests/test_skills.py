"""The contract every skill document must satisfy, plus the survey skill.

Structural and topic-presence only. Where a test insists on a word it is because
the ticket requires that instruction to exist, never because of how it reads.
"""

import pytest

from support import (
    CONTEXT,
    document,
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
MAP = PLUGIN_ROOT / "skills" / "map" / "SKILL.md"


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

    def test_body_keeps_room_for_the_next_rule(self, skill):
        """Warn at 2460, not at 2500, so the wall is seen before it is hit.

        Two skills sat within ten words of the ceiling and every change to them
        cost a deletion somewhere else. Four separate trims were needed to land
        sixty words in one, and twice a paragraph could not be moved out because
        a test held it in place — so the squeeze was discovered mid-edit, under
        pressure, which is when the wrong sentence gets cut. One was: the clause
        forbidding batched row writes went, judged a duplicate, and the next run
        did exactly what only that clause forbade.

        Failing early turns that into a decision made deliberately, with the
        whole section in view.
        """
        words = len(_body(skill).split())
        assert words < 2460, (
            f"skill body is {words} words, within {2500 - words} of the hard "
            "limit. Move a section into references/ *with its tests* before "
            "adding more, rather than trimming whatever is nearest."
        )

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
    # Two documents depend on this procedure to decide a check was gained, and
    # the worked example is invisible in the help surface, so the procedure
    # must say so rather than let them assume it is detectable.
    assert "cannot show a new rule inside an existing command" in body, (
        "the probe must state what its help-surface comparison cannot see"
    )


def test_the_glossary_keeps_validity_and_tenant_acceptance_apart():
    # These are two of ADR-0001's five checks, ordered apart because they see
    # different things and need different resources. The glossary defined
    # Validity as both, so the plugin's vocabulary and its check order
    # disagreed about what the word meant.
    body = CONTEXT.read_text(encoding="utf-8")
    entry = body.split("**Validity**:")[1].split("_Avoid_")[0].lower()
    assert "legal in the format" in entry
    assert "separate" in entry, (
        "Validity must not absorb tenant acceptance; they are two checks"
    )


def test_every_migration_directory_file_has_a_skeleton():
    body = (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")
    for filename in MIGRATION_DIRECTORY_FILES:
        stem = filename.replace(".md", "")
        heading = "# " + stem.replace("-", " ")
        assert f"`{filename}`:" in body or heading.lower() in body.lower(), (
            f"{filename} has no skeleton, so each skill will invent a different one"
        )


# --- the Conversion queue and the row Version --------------------------------
#
# ADR-0012 delivers a Migration one Conversion at a time. These assert the two
# files and the one column that order depends on, and the reasons a later edit
# would most cheaply drop. Presence and bindingness only, never wording.

class TestScenariosAndAssembledAreDeclared:
    def _directory(self):
        return (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")

    def test_both_files_are_in_the_single_constant(self):
        # The constant is what every other test module reads, so a file missing
        # here is a file with no contract coverage anywhere.
        assert "scenarios.md" in MIGRATION_DIRECTORY_FILES
        assert "assembled.md" in MIGRATION_DIRECTORY_FILES

    def test_scenarios_is_both_the_incidence_and_the_queue(self):
        # One table rather than two, because "what is left" and "what would it
        # cost" are asked together and one read must answer both.
        assert has_paragraph_with(self._directory(), "scenarios.md", "incidence", "queue")

    def test_the_four_scenario_statuses_are_the_complete_set(self):
        # resume counts the rows in each state, so a private fifth value is
        # counted as none of them.
        body = self._directory()
        assert has_paragraph_with(
            body, "`pending`", "`done`", "`parked`", "`out-of-scope`", "complete set"
        )

    def test_one_reason_column_serves_parked_and_out_of_scope_alike(self):
        assert has_paragraph_with(self._directory(), "`reason`", "`parked`", "`out-of-scope`")

    def test_the_unseen_count_is_computed_and_never_stored(self):
        # A stored count is stale the moment any Conversion finishes, and a
        # stale count does not announce itself — it mis-orders the queue.
        assert has_paragraph_with(
            self._directory(), "unseen", "computed", "never stored", "stale"
        )

    def test_assembled_records_the_row_versions_a_test_consumed(self):
        # Versions rather than rows, because that is what makes "this test was
        # built on a superseded decision" a comparison rather than a reading.
        assert has_paragraph_with(self._directory(), "assembled.md", "versions", "consumed")

    def test_assembled_is_what_makes_a_corrected_rows_dependents_findable(self):
        assert has_paragraph_with(
            self._directory(), "dependents", "findable", "working copy"
        )


class TestTheStepMapCarriesAVersion:
    def _directory(self):
        return (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")

    def test_the_skeleton_has_a_version_column_beside_status(self):
        header = next(
            line for line in self._directory().splitlines()
            if line.startswith("| Source Step |") and "Expression" in line
        )
        columns = [cell.strip() for cell in header.strip("|").split("|")]
        assert "Version" in columns, f"the Step Map cannot version a row: {header}"
        assert columns.index("Version") == columns.index("Status") + 1, (
            f"Version must sit beside Status: {header}"
        )

    def test_the_bump_rule_names_expression_and_status(self):
        assert has_paragraph_with(
            self._directory(), "version", "bumped", "expression", "status"
        )

    def test_occurrence_counts_and_provenance_never_bump_it(self):
        # They change every Conversion, so a version churning on them would
        # re-assemble the suite for nothing.
        assert has_paragraph_with(
            self._directory(), "never bumped", "occurrence", "provenance"
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

    def test_it_screens_for_unconvertible_scenarios_before_quoting_a_size(self):
        # The screen is survey's to run; how to run it is a reference, because
        # the skill body is a progressive-disclosure budget and the anecdotes
        # that justify the classifier are not needed to decide to screen.
        body = _body(SURVEY)
        assert has_paragraph_with(
            body, "screen for what is unconvertible", "before quoting a size"
        )
        assert has_paragraph_with(
            body, "screen for what is unconvertible", "references/content-screen.md"
        ), "survey must point at the procedure rather than drop it"

    def test_the_content_screen_reference_keeps_the_procedure(self):
        # Measured: six of seven web-only scenarios seeded data by rewriting a
        # spreadsheet and importing it, which the platform cannot do.
        body = (REFERENCES_DIR / "content-screen.md").read_text(encoding="utf-8")
        assert has_paragraph_with(body, "spreadsheet", "out of scope")
        assert has_paragraph_with(
            body, "step-definition names", "text of a line"
        ), "a classifier on free text excluded a web test for containing Mobile"
        assert has_paragraph_with(
            body, "`out-of-scope`", "reason", "never omitted", absent=("omit it",)
        ), "a screened scenario must be seeded, not dropped"

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


# --- the triage axis ---------------------------------------------------------
#
# survey screened step *content* and never asked what application type the suite
# targets, so it could green-light a Migration that `attach` refuses on day one:
# the CLI declares a catalogue for web and unified applications only, and every
# other platform occupies a non-overlapping template-id block, so three
# catalogues are missing rather than one.

class TestSurveyScreensTheTargetPlatform:
    def _refusals(self):
        return TestSurveySkill()._refusals()

    def test_it_refuses_a_suite_whose_platform_has_no_catalogue(self):
        assert has_paragraph_with(
            self._refusals(),
            "platform",
            "stop",
            absent=("do not refuse", "proceed anyway", "warn only"),
        ), (
            "the refusals section never screens the target platform, so a survey "
            "can size a Migration the first attach refuses"
        )

    def test_the_platform_gate_names_the_two_kinds_of_application_it_can_convert(self):
        assert has_paragraph_with(self._refusals(), "web", "unified"), (
            "a platform gate that does not say which platforms are convertible "
            "cannot be acted on"
        )

    def test_it_asks_the_operator_which_application_the_migration_targets(self):
        # The suite's own source cannot settle this: the target application is a
        # thing in their tenant, so it is an Application Fact, not a probe.
        assert has_paragraph_with(self._refusals(), "operator", "which application")

    def test_the_convertible_set_is_probed_and_not_pinned(self):
        # ADR-0003. A set hardcoded here is a set that is wrong the day a
        # catalogue lands, and wrong in a document nobody re-reads.
        body = _body(SURVEY)
        assert has_paragraph_with(body, "catalogue", "platform-facts.md"), (
            "the convertible set must be recorded as a probed Platform Fact"
        )

    def test_the_platform_gate_precedes_the_content_screen(self):
        # Cheapest-decisive first: the content screen reads the whole suite, and
        # is wasted effort on a suite that could never attach.
        body = _body(SURVEY)
        gate = body.lower().index("platform")
        screen = body.lower().index("screen for what is unconvertible")
        assert gate < screen

    def test_the_content_screen_says_which_axis_it_screens(self):
        # It is still a correct screen, and was never the whole of triage. Left
        # unqualified, its presence reads as though platform were covered.
        assert has_paragraph_with(
            _body(SURVEY), "screen for what is unconvertible", "platform"
        ), "the content screen must not read as the whole of triage"

    def test_the_probe_records_which_platforms_the_build_writes(self):
        body = (REFERENCES_DIR / "cli-probe.md").read_text(encoding="utf-8").lower()
        assert "applicationtype" in body or "application type" in body, (
            "the probe records what the build checks but not what it can write"
        )
        assert "tss1609" in body, (
            "the diagnostic that proves the refusal is real belongs in the "
            "reference, never in front of the Operator"
        )


def test_the_glossary_has_a_term_for_the_catalogue_a_platform_has():
    # The platform gate in survey turns on it, and a gate whose central noun is
    # undefined is a gate two readers will draw differently.
    body = CONTEXT.read_text(encoding="utf-8")
    assert "**Catalogue**:" in body, "survey refuses on a term the glossary never defines"
    entry = body.split("**Catalogue**:")[1].split("**")[0].lower()
    assert "platform" in entry
    assert "refus" in entry, (
        "an absent catalogue is a refusal rather than a gap, and the term must say so"
    )


# --- residue tells a gap from a refusal --------------------------------------
#
# The format's own maintainers draw a line the Residue model lacked: a
# capability a later ticket fills is a gap, a construct declined on purpose is a
# refusal. Both stop a run and only one is temporary, so recording them
# identically means re-examining a settled decision every session and never
# noticing when a gap has closed.

def test_residue_says_whether_a_cause_is_temporary():
    body = (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")
    header = next(
        line for line in body.splitlines()
        if line.startswith("| Source Step |") and "Cause" in line
    )
    assert "Standing" in header, f"residue.md cannot say whether a cause can close: {header}"
    assert has_paragraph_with(body, "gap", "refusal", "revisit"), (
        "the two standings must differ in what re-examines them"
    )


def test_the_glossary_keeps_a_gap_and_a_refusal_apart():
    entry = CONTEXT.read_text(encoding="utf-8").split("**Residue**:")[1].split("_Avoid_")[0].lower()
    assert "gap" in entry and "refusal" in entry, (
        "Residue absorbs both, so a permanent decision and a missing feature "
        "are recorded and re-read identically"
    )


def test_the_probe_calls_the_missing_catalogues_a_gap():
    # wishlist 0008 says the three catalogues "remain the work", so they are a
    # gap that presents as a refusal today, not a construct declined on purpose.
    body = (REFERENCES_DIR / "cli-probe.md").read_text(encoding="utf-8")
    assert not has_paragraph_with(body, "a refusal and not a gap"), (
        "the missing catalogues are tracked work; calling them permanent tells "
        "a later session never to look again"
    )
    assert has_paragraph_with(body, "catalogue", "gap")


def test_the_probe_does_not_undercount_the_cli_surface():
    body = (REFERENCES_DIR / "cli-probe.md").read_text(encoding="utf-8")
    # The dispatch has seven commands; the table named four and read as the
    # whole surface, which is how a probe misses `list`.
    for command in ("run", "url", "list"):
        assert f"`{command}`" in body, f"the probe never mentions {command}"


# The Standing of an unresolved element was asserted here, against the skill,
# and separately against map — two callers, and not the document that owns what
# happens when nothing resolves. It moved to references/element-resolution.md
# and is asserted in tests/test_element_resolution.py.


def test_the_glossary_has_a_term_for_a_value_kind():
    # map and authoring.md both turn on it, and a term two documents use is a
    # term the glossary owns.
    body = CONTEXT.read_text(encoding="utf-8")
    assert "**Value Kind**:" in body
    entry = body.split("**Value Kind**:")[1].split("_Avoid_")[0].lower()
    assert "slot" in entry, "a value kind is a property of the slot, not of the value alone"


def test_the_two_documents_agree_on_the_standing_of_a_missing_catalogue():
    # They disagreed: the glossary said "refused", the probe said "gap", and a
    # later session reading either one alone drew the opposite conclusion. The
    # answer is that the refusal is the behaviour and the gap is the standing.
    entry = CONTEXT.read_text(encoding="utf-8").split("**Catalogue**:")[1].split("_Avoid_")[0]
    assert "gap" in entry.lower(), (
        "the glossary must say a missing catalogue is a gap, since that is what "
        "decides whether anyone looks again"
    )
    assert has_paragraph_with(entry, "refus", "gap"), (
        "both words must sit in one instruction, or the entry reads as one and "
        "the probe as the other"
    )


#: The five things a Step Map row carries. Asserted against the document that
#: defines the schema — a new column is added there, not in a caller. This
#: parametrisation was in test_map_skill.py, which is what obliged `map` to
#: restate the schema it points at.
ROW_COLUMNS = ("source", "occurrence", "parameter", "expression", "status")


@pytest.mark.parametrize("column", ROW_COLUMNS)
def test_the_step_map_row_carries_each_of_the_five_things(column):
    body = (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")
    section = [v for k, v in markdown_sections(body).items() if "file" in k.lower()]
    haystack = (section[0] if len(section) == 1 else body).lower()
    assert column in haystack, (
        f"a row must carry {column}, so reviewing it does not mean going back "
        f"to the source"
    )


#: Definitional phrases CONTEXT.md owns. A skill carrying one is restating the
#: vocabulary rather than using it — which is how map's Steps 6 and 7 came to
#: hold ~110 words of the glossary, with both copies asserted.
#:
#: Verbatim copies only: a paraphrase of the same distinction is not catchable
#: by string matching, and this control says so rather than implying it covers
#: more than it does.
GLOSSARY_PHRASES = (
    "unrecorded concession is a divergence",
    "no entry is final",
    "a build change can close a gap and can never close a refusal",
    "**step addon** adds a verb",
)


@pytest.mark.parametrize("phrase", GLOSSARY_PHRASES)
def test_the_glossary_states_each_definition_it_owns(phrase):
    assert phrase in " ".join(CONTEXT.read_text(encoding="utf-8").split()).lower(), (
        f"the glossary is supposed to own {phrase!r} and does not state it"
    )


@pytest.mark.parametrize("skill", skill_files(), ids=lambda p: p.parent.name)
@pytest.mark.parametrize("phrase", GLOSSARY_PHRASES)
def test_no_skill_restates_a_definition_the_glossary_owns(phrase, skill):
    body = " ".join(_body(skill).split()).lower()
    assert phrase not in body, (
        f"{skill.parent.name} restates {phrase!r}, which CONTEXT.md owns; a "
        f"skill uses the vocabulary rather than defining it"
    )


#: The fixed Residue causes. A cause written as prose reads fine to whoever
#: wrote it and cannot be counted, sorted, or handed to the person who can close
#: it — and the first two below are the pair that get merged by accident, since
#: both present as a step that will not finish and neither is the other's work.
RESIDUE_CAUSES = (
    "step addon",
    "data generator addon",
    "unresolved element",
    "no catalogue",
    "declined",
)


@pytest.mark.parametrize("cause", RESIDUE_CAUSES)
def test_the_migration_directory_defines_every_residue_cause(cause):
    body = (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")
    assert cause in body.lower(), (
        f"{cause!r} is not defined where the Residue table lives, so each stage "
        f"will invent its own wording for it"
    )


def test_the_two_addon_causes_are_distinguished_not_merged():
    body = (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8").lower()
    # Both must be present *and* the difference stated. Listing them adjacently
    # in a table is what a merge looks like right before it happens.
    assert "step addon" in body and "data generator addon" in body
    assert "different" in body, (
        "the table must say the two addon causes are different requests, or the "
        "distinction is decoration"
    )


def test_the_glossary_owns_what_an_addon_is():
    body = " ".join(CONTEXT.read_text(encoding="utf-8").split()).lower()
    assert "**addon**" in body
    assert "data generator addon" in body, (
        "an Addon that names only the step kind leaves the generator kind with "
        "no word, which is how the two get recorded as one cause"
    )


class TestSurveySeedsTheConversionQueue:
    """`scenarios.md` is seeded by survey, from the incidence it already walks.

    Survey is the only stage that reads every line of the suite. The incidence
    it used to discard is what orders the Conversions, and nothing downstream
    can rebuild it without a second walk of tens of thousands of lines.
    """

    def _survey(self):
        return " ".join(document(SURVEY).flat.split()).lower()

    def test_the_incidence_is_recorded_in_the_pass_survey_already_makes(self):
        assert has_paragraph_with(
            _body(SURVEY), "incidence", "same pass", "second pass"
        ), (
            "recording the incidence must cost one column in the existing walk, "
            "never a second walk of the source"
        )

    def test_it_seeds_one_row_per_scenario_as_pending(self):
        assert has_paragraph_with(
            _body(SURVEY), "`scenarios.md`", "per scenario", "`pending`"
        )

    def test_an_unconvertible_scenario_is_seeded_out_of_scope_with_its_reason(self):
        # Never omitted: an absent row reads as "nobody looked". The rule is
        # stated where the screen is, and survey states the seeding it does.
        assert has_paragraph_with(
            _body(SURVEY), "`scenarios.md`", "`out-of-scope`", "reason"
        )
        assert has_paragraph_with(
            (REFERENCES_DIR / "content-screen.md").read_text(encoding="utf-8"),
            "`out-of-scope`",
            "reason",
            "never omitted",
            absent=("omit it",),
        )

    def test_the_step_map_seeding_is_stated_as_unchanged(self):
        # The denominator and the anti-stall signal both depend on every
        # distinct Source Step having a visibly unfilled row, in scope or not.
        assert has_paragraph_with(
            _body(SURVEY), "step map", "unchanged", "`unreviewed`"
        )

    def test_it_commits_the_new_file_with_the_rest(self):
        assert has_paragraph_with(_body(SURVEY), "commit `scenarios.md`")

    def test_the_report_says_how_many_are_in_scope_and_how_many_were_ruled_out(self):
        body = self._survey()
        assert "in scope to convert" in body and "ruled out" in body, (
            "the Operator reports a scenario count to the customer; survey is "
            "where that count first exists"
        )


class TestTheStepMapIsSeededBeforeMapping:
    """Survey writes the rows; mapping fills them.

    A measured run read step definitions across 118 tool calls, wrote no row,
    and ended with nothing — every resolved locator and traced helper went with
    the session. An empty map and a map nobody has started look identical, so
    there was no moment at which the run was visibly not progressing.

    Seeding costs one write, since survey has just enumerated the distinct
    Source Steps, and it makes `reviewed n of m` answerable from the first
    minute.
    """

    def _survey(self):
        return " ".join(document(SURVEY).flat.split())

    def _map(self):
        return " ".join(document(MAP).flat.split())

    def test_survey_seeds_the_map(self):
        body = self._survey()
        assert "seed `step-map.md`" in body or "seed step-map.md" in body, (
            "the enumeration already holds the rows; writing them is one step"
        )
        assert "unreviewed" in body

    def test_mapping_fills_rows_rather_than_creating_them(self):
        assert "seeded" in self._map(), (
            "mapping that still creates rows leaves the count at zero until it "
            "finishes, which is the state that hid the failure"
        )

    def test_mapping_writes_a_row_before_opening_the_next(self):
        body = self._map()
        assert "before opening the next" in body, (
            "batching is what lost the work; the instruction has to name the "
            "boundary, not just recommend writing things down"
        )

    def test_the_directory_reference_describes_the_seeding(self):
        body = (REFERENCES_DIR / "migration-directory.md").read_text(encoding="utf-8")
        assert "Seeded by survey" in body
