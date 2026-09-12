"""The eval cases, checked for well-formedness.

`claude plugin eval` is gated on early access and is not enabled for this
account, so these cases cannot be run here. They are still files, and a file
that will not parse the day the gate opens is worth catching now.

What this suite can check: that every case parses, that its graders name types
the runner supports, that every path a case points at exists, that the
deterministic assertions the ticket requires are actually present, and that no
fixture carries data from a real suite. What it cannot check: whether a grader
does what its author meant. That is what the gate is for.
"""

import pytest
import subprocess

import yaml

from support import PLUGIN_ROOT, FIXTURES_DIR, has_paragraph_with, hedges_in, preamble

EVALS_DIR = PLUGIN_ROOT / "evals"
EVAL_README = EVALS_DIR / "README.md"

#: Grader types the runner supports. Four are deterministic and two are
#: model-judged; the split is what decides what a case may honestly assert.
DETERMINISTIC_GRADERS = ("regex", "tool_used", "tool_order", "file_exists")
JUDGED_GRADERS = ("llm", "baseline")
GRADER_TYPES = DETERMINISTIC_GRADERS + JUDGED_GRADERS


def case_dirs():
    """Every eval case: a directory holding a prompt.md.

    prompt.md plus graders/*.md is the layout `claude plugin eval --help` names,
    with case.yaml carrying only what prompt frontmatter cannot — the context.
    Inline `graders:` in case.yaml is not part of the documented surface, so it
    is not used here.
    """
    if not EVALS_DIR.is_dir():
        return []
    return sorted(p.parent for p in EVALS_DIR.glob("*/prompt.md"))


def _frontmatter(path):
    from support import split_frontmatter

    meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    return meta, body


def _case_yaml(directory):
    path = directory / "case.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _graders(directory):
    return sorted((directory / "graders").glob("*.md"))


CASES = case_dirs()


def test_there_are_cases():
    assert CASES, "no eval cases found; every check below would prove nothing"


def test_what_the_first_real_run_settled_is_written_down(self=None):
    """The three guesses the cases shipped with, and what each turned out to be.

    All three were written from `--help` and from the shape of other eval
    suites, and all three were plausible. The value of recording them is that
    each one failed *silently* in a different way — one refused to load, one
    loaded and measured nothing, and one needed a flag nobody would guess — and
    a suite that has never been run carries an unknown number more.
    """
    assert EVAL_README.is_file(), "the next person needs to know how to run these"
    body = EVAL_README.read_text(encoding="utf-8")

    # An enum, not prose. This is what stopped every case from loading.
    assert has_paragraph_with(body, "focus", "enum"), (
        "it must say an llm grader's focus is an enum rather than a sentence"
    )
    # The dangerous one: the cases loaded, ran, and scored zero in both arms.
    # A case that fails identically with and without the plugin measures
    # nothing, and reads as a plugin failure rather than a case failure.
    assert has_paragraph_with(body, "add_dirs", "does not seed"), (
        "it must say add_dirs grants access rather than seeding the workspace"
    )
    assert has_paragraph_with(body, "scaffold_script", "--scaffold"), (
        "it must say what puts files in cwd, and that it needs the flag"
    )


def test_the_schema_is_written_down_rather_than_guessed(self=None):
    """Three guesses, three defects. The record is cheaper than a fourth.

    Every fault in this suite came from inferring the schema from `--help` and
    from the shape of other eval suites. Two of them were silent: an ignored
    `context` key looks exactly like a working one, and a `focus` left at its
    default turns a strict criterion into a weak one with no warning.
    """
    body = EVAL_README.read_text(encoding="utf-8")
    for field in ("trace", "last_message", "files", "mock_calls"):
        assert field in body, f"the focus/target enum is incomplete: {field}"
    assert "with-only" in body and "both" in body, "the arm values are unrecorded"
    assert has_paragraph_with(body, "no alternation"), (
        "tool_order names one tool, so the verb is part of the assertion"
    )
    assert has_paragraph_with(body, "are ignored", "misspelled"), (
        "an ignored context key is the silent failure and must be called out"
    )


def test_the_readme_says_how_to_run_them(self=None):
    body = EVAL_README.read_text(encoding="utf-8")
    # An operator grant on top of each case's allowed_tools. Without it a case
    # listing Write still does not get one, and the tool_order graders that
    # need a Write in the trace cannot pass.
    assert "--allow-tools" in body and "--scaffold" in body


def test_the_readme_explains_why_ablation_is_the_point(self=None):
    body = EVAL_README.read_text(encoding="utf-8")
    # For a plugin that is only instructions, the delta between the two arms is
    # the only measure of whether an instruction earns its place.
    assert has_paragraph_with(body, "without the plugin", "delta")
    assert has_paragraph_with(body, "unprompted", "earned nothing")


def test_the_readme_says_when_they_run(self=None):
    body = EVAL_README.read_text(encoding="utf-8")
    assert has_paragraph_with(
        body, "on demand", "never on every", absent=("run them on every commit",)
    )


def test_the_readme_preamble_grants_no_exception(self=None):
    assert not hedges_in(preamble(EVAL_README.read_text(encoding="utf-8")))


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
class TestEveryCase:
    def test_its_prompt_frontmatter_parses(self, case):
        meta, body = _frontmatter(case / "prompt.md")
        assert isinstance(meta, dict)
        assert body.strip(), "the case asks the agent nothing"

    def test_its_name_matches_its_directory(self, case):
        meta, _ = _frontmatter(case / "prompt.md")
        assert meta.get("name") == case.name

    def test_it_runs_more_than_once(self, case):
        # Model-judged graders are noisy; a single run turns one flaky verdict
        # into a suite failure.
        meta, _ = _frontmatter(case / "prompt.md")
        assert meta.get("runs", 3) >= 3

    def test_it_is_tagged_so_it_can_be_filtered(self, case):
        meta, _ = _frontmatter(case / "prompt.md")
        assert meta.get("tags"), "an untagged case cannot be run selectively"

    def test_it_bounds_its_own_run(self, case):
        # --max-cost-usd is a ceiling on the whole run; these bound each case,
        # so one case cannot spend the budget the others need.
        meta, _ = _frontmatter(case / "prompt.md")
        assert meta.get("max_turns"), "an unbounded case can run away"
        assert meta.get("timeout_seconds"), "an unbounded case can hang"

    def test_it_grants_only_the_tools_it_needs(self, case):
        meta, _ = _frontmatter(case / "prompt.md")
        allowed = meta.get("allowed_tools") or []
        assert allowed, "a case that grants nothing cannot read the fixture"
        assert "Skill" in allowed, "the plugin arm needs the Skill tool to route"

    def test_it_has_graders(self, case):
        assert _graders(case), "a case with no graders always passes"

    def test_every_grader_names_a_supported_type(self, case):
        for grader in _graders(case):
            meta, _ = _frontmatter(grader)
            assert meta.get("type") in GRADER_TYPES, (
                f"{grader.name}: {meta.get('type')!r} is not a grader type the "
                f"runner supports"
            )

    def test_every_grader_says_why_it_exists(self, case):
        # The body of a grader file is its rubric or its rationale. A grader
        # nobody can explain is a grader nobody will fix when it starts failing.
        for grader in _graders(case):
            _, body = _frontmatter(grader)
            assert len(body.split()) >= 15, f"{grader.name} does not say why it exists"

    def test_it_carries_at_least_one_deterministic_grader(self, case):
        types = {_frontmatter(g)[0].get("type") for g in _graders(case)}
        assert types & set(DETERMINISTIC_GRADERS), (
            "deterministic graders carry the weight; a case scored only by model "
            "judgement is a coin flip"
        )

    def test_every_judged_grader_states_a_narrow_criterion(self, case):
        for grader in _graders(case):
            meta, _ = _frontmatter(grader)
            if meta.get("type") not in JUDGED_GRADERS:
                continue
            criteria = str(meta.get("criteria") or "")
            assert criteria.strip(), "a judged grader with no criteria judges nothing"
            # Narrow means it says what it is looking for and what to ignore.
            # "Did it do a good job" is the flakiness this budget cannot afford.
            assert len(criteria.split()) >= 25, (
                f"{grader.name}: the criteria are {len(criteria.split())} words; "
                f"write them narrowly or the grader becomes a coin flip"
            )
            assert "ignore" in criteria.lower() or "does not count" in criteria.lower(), (
                f"{grader.name}: say what the judge should ignore, or it will "
                f"judge the whole response"
            )

    def test_a_skill_grader_states_its_arm_rather_than_relying_on_a_default(self, case):
        """The key exists; an earlier test asserted it did not.

        `--help` says only that graders marked with-only, "incl. `tool_used:
        Skill`", are treated as a plugin-fired indicator. From that this suite
        concluded the YAML key was undocumented and forbade inventing one —
        reasonable at the time, and wrong: the runner's own schema takes
        `arm: with-only | both` on every grader type.

        Stating it matters because a Skill call cannot happen in the no-plugin
        arm. Scored, it would guarantee a delta that measures nothing about the
        instructions, which is the one thing the ablation exists to avoid.
        """
        for grader in _graders(case):
            meta, _ = _frontmatter(grader)
            if meta.get("type") == "tool_used" and meta.get("tool") == "Skill":
                assert meta.get("arm") == "with-only", (
                    f"{grader.name}: a Skill grader must declare arm: with-only, "
                    "or it scores a delta that only reflects the plugin being loaded"
                )

    def test_it_scaffolds_its_fixture_into_the_run(self, case):
        # Settled by running the suite for the first time. The workspace starts
        # empty, and `add_dirs` grants read access to a path rather than seeding
        # it — a case carrying only add_dirs had the agent glob an empty cwd and
        # correctly refuse to map anything, scoring zero in both arms and
        # measuring nothing. `scaffold_script` is what puts files in cwd.
        context = _case_yaml(case).get("context") or {}
        assert "add_dirs" not in context, (
            f"{case.name} uses add_dirs to seed the workspace; it only grants "
            "read access, so the agent sees an empty working directory"
        )
        script = context.get("scaffold_script")
        assert script, f"{case.name} scaffolds no fixture into the run"
        resolved = case / script
        assert resolved.is_file(), f"{script} does not exist (resolved {resolved})"

    def test_its_turn_budget_clears_what_the_plugin_arm_actually_uses(self, case):
        """Measured, not guessed. The budget was 20 and biased the ablation.

        In the first real ablation every with-plugin run reached or passed 20
        turns (17, 20, 34, 33, 21) while the no-plugin arm sat well under it
        (21, 15, 23, 15, 20). That is the plugin working — it sends the agent to
        open the helper the source line hides — and a budget set at the
        baseline's cost cuts off exactly the behaviour the case exists to
        measure, then scores the truncation as a failure.

        A budget that penalises one arm is worse than no budget: the number it
        produces reads as evidence about the plugin.
        """
        meta, _ = _frontmatter(case / "prompt.md")
        assert meta.get("max_turns", 0) >= 40, (
            f"{case.name}: max_turns is {meta.get('max_turns')}; the with-plugin "
            "arm has been measured at up to 34 turns, so this truncates the arm "
            "under test and scores the truncation against it"
        )

    def test_its_scaffold_is_valid_bash_that_finds_its_own_directory(self, case):
        """Both halves were broken at once, by one careless generator.

        A templating pass that substituted the fixture name replaced it inside
        `${BASH_SOURCE[0]}` too, giving `${BASH_cucumber-java[0]}`. Bash reads
        that as the default-value form `${var-default}` — so it expanded to the
        string `java[0]`, `dirname` returned `.`, and every path resolved
        against the workspace instead of the case directory. It is valid bash,
        it fails no syntax check, and `set -u` does not catch it because the
        default-value form is exactly how you avoid an unset variable.

        The whole suite failed this way with a scaffold error and no model
        turns, which is the cheap version of the failure. The expensive version
        is a scaffold that half-works.
        """
        script = case / "scaffold.sh"
        assert script.is_file()
        body = script.read_text(encoding="utf-8")
        assert "${BASH_SOURCE[0]}" in body, (
            f"{case.name}/scaffold.sh does not resolve its own directory from "
            "BASH_SOURCE; a mangled expansion resolves against the workspace"
        )
        assert subprocess.run(["bash", "-n", str(script)]).returncode == 0

    def test_its_scaffold_actually_populates_a_directory(self, case, tmp_path):
        # Run it. Every check above reads the script; none of them would catch
        # a cp that silently copies nothing, and "the eval ran and measured an
        # empty workspace" is the failure mode that reads as a plugin defect.
        result = subprocess.run(["bash", str((case / "scaffold.sh").resolve())],
                                cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert (tmp_path / ".testsigma" / "migration").is_dir(), (
            f"{case.name}/scaffold.sh left no Migration Directory in the workspace"
        )
        assert any(tmp_path.glob("*/*")), (
            f"{case.name}/scaffold.sh copied no source suite into the workspace"
        )

    def test_every_fixture_its_scaffold_copies_exists(self, case):
        script = (case / ((_case_yaml(case).get("context") or {})
                          .get("scaffold_script") or "scaffold.sh"))
        for line in script.read_text(encoding="utf-8").splitlines():
            if not line.strip().startswith("cp "):
                continue
            source = line.split('"$here/')[1].split('"')[0].rstrip("/.")
            assert (case / source).is_dir(), (
                f"{case.name} scaffolds {source}, which does not exist"
            )

    def test_its_fixtures_match_the_canonical_ones(self, case):
        # The cases hold their own copies because the runner refuses an
        # add_dirs or scaffold path containing `..`. One fixture edited in the
        # repository and not here would leave the eval measuring a suite
        # nothing else has seen, silently.
        EVALS = EVALS_DIR
        canonical = {
            "migration-part-done": EVALS / "fixtures" / "migration-part-done",
            "cucumber-java": PLUGIN_ROOT / "tests" / "fixtures" / "cucumber-java",
            "tosca-subset-export": (PLUGIN_ROOT / "tests" / "fixtures"
                                    / "tosca-subset-export"),
        }
        for copy in sorted((case / "fixtures").glob("*")):
            source = canonical[copy.name]
            ours = sorted(p.relative_to(copy) for p in copy.rglob("*") if p.is_file())
            theirs = sorted(p.relative_to(source) for p in source.rglob("*")
                            if p.is_file())
            assert ours == theirs, (
                f"{case.name}/fixtures/{copy.name} has drifted from {source}; "
                "run evals/sync-fixtures.py"
            )
            for relative in ours:
                assert (copy / relative).read_bytes() == (source / relative).read_bytes(), (
                    f"{case.name}/fixtures/{copy.name}/{relative} differs from "
                    "the canonical fixture; run evals/sync-fixtures.py"
                )


# --- how they are run ---------------------------------------------------------

WORKFLOW = PLUGIN_ROOT.parents[1] / ".github" / "workflows" / "testsigma-evals.yml"


def _workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_a_workflow_runs_them_on_demand_and_on_document_changes():
    assert WORKFLOW.is_file(), "nothing runs these"
    # PyYAML reads the `on:` key as the boolean True, which is a YAML 1.1 quirk
    # rather than a mistake in the file.
    triggers = _workflow().get("on", _workflow().get(True))
    assert "workflow_dispatch" in triggers, "they must be runnable on demand"
    assert "pull_request" in triggers, "they must run when a document changes"
    assert "push" not in triggers, "they must not run on every commit"


def test_the_paths_filter_covers_the_documents_that_change_behaviour():
    triggers = _workflow().get("on", _workflow().get(True))
    paths = triggers["pull_request"]["paths"]
    # Exact entries, not substring containment: an added exclusion pattern such
    # as '!plugins/testsigma/skills/experimental/**' contains the substring
    # while the positive glob it replaced no longer triggers anything.
    # The plugin is instructions, so these are the only files that can change
    # what an agent does.
    for directory in ("skills", "commands", "adapters", "references", "evals"):
        wanted = f"plugins/testsigma/{directory}/**"
        assert wanted in paths, f"{wanted} is not watched; paths are {paths}"
    assert not [p for p in paths if p.startswith("!")], (
        "an exclusion pattern here silently narrows what triggers a run"
    )


def test_the_eval_job_is_skipped_rather_than_passing_while_gated():
    # ADR-0001 applied to the plugin's own CI: a check that could not run must
    # never read as a pass. A skipped job shows as skipped, not green.
    jobs = _workflow()["jobs"]
    assert "if" in jobs["evals"], "the eval job runs unconditionally and will fail"
    # Polarity, not presence. Inverted, this would run the paid job exactly when
    # the account is not enrolled, and the old assertion could not tell.
    assert jobs["evals"]["if"].strip() == "vars.PLUGIN_EVAL_ENROLLED == 'true'", (
        f"the eval job's condition is {jobs['evals']['if']!r}"
    )
    assert jobs["not-checked"]["if"].strip() == "vars.PLUGIN_EVAL_ENROLLED != 'true'", (
        f"the not-checked job's condition is {jobs['not-checked']['if']!r}"
    )
    assert any(
        "NOT CHECKED" in str(step) for step in jobs["not-checked"]["steps"]
    ), "a green pull request must not be mistaken for a checked one"


def test_the_run_is_cost_capped_and_scored():
    # Scoped to the step that actually invokes the runner. Checked against the
    # whole file, a comment mentioning the flags would satisfy this after they
    # were removed from the command.
    steps = _workflow()["jobs"]["evals"]["steps"]
    # Shell comments stripped: scoping to `run:` was not enough, because a
    # comment inside the run block still contains the flag names. A commented
    # -out flag is exactly the regression this is guarding against.
    lines = [
        line
        for step in steps
        for line in str(step.get("run", "")).splitlines()
        if not line.strip().startswith("#")
    ]
    commands = " ".join(lines)
    assert "claude plugin eval" in commands, "the job does not run the evals"
    assert "--max-cost-usd" in commands, "an uncapped run can spend without limit"
    assert "--threshold" in commands, "an unscored run gives CI no pass or fail"


# --- the fixtures -------------------------------------------------------------

MIGRATION_FIXTURE = EVALS_DIR / "fixtures" / "migration-part-done" / ".testsigma" / "migration"


def test_both_source_fixtures_are_shared_with_the_pytest_suite():
    # One hand-built example of each format, not two that can drift.
    assert (FIXTURES_DIR / "cucumber-java").is_dir()
    assert (FIXTURES_DIR / "tosca-subset-export").is_dir()


def test_the_part_done_migration_fixture_is_complete():
    from support import MIGRATION_DIRECTORY_FILES

    assert MIGRATION_FIXTURE.is_dir(), "the refusal case needs a Migration already begun"
    present = {p.name for p in MIGRATION_FIXTURE.glob("*.md")}
    assert present == set(MIGRATION_DIRECTORY_FILES), (
        f"the fixture's directory does not match the real shape: {present}"
    )


def test_the_part_done_fixture_carries_an_unresolved_element():
    # Without one, the refusal case cannot refuse anything.
    residue = (MIGRATION_FIXTURE / "residue.md").read_text(encoding="utf-8")
    assert "unresolved element" in residue
    # `"reviewed" in text` is also true when every row reads `unreviewed`,
    # which is the opposite state. Match the cell.
    step_map = (MIGRATION_FIXTURE / "step-map.md").read_text(encoding="utf-8")
    assert "| reviewed |" in step_map, (
        "assembly needs a genuinely reviewed row, or it would refuse for the "
        "wrong reason"
    )


#: Shapes that would mean text came from a real suite rather than being
#: hand-built. Checked because this plugin is published, and the source material
#: its examples imitate is a customer's.
#:
#: Two kinds sit here together. Credentials and hosts are obvious. The rest are
#: vocabulary lifted from one customer's domain and code — a system name, an
#: identifier style, a test-case prefix. Those are the ones that actually got
#: through, because an author writing prose reaches for the example they have
#: been staring at all week, and cannot see that it is theirs and not everyone's.
FORBIDDEN_ANYWHERE = (
    "dhl",
    "mawm",
    "manh",
    "exldd",
    "exlds",
    "ilpn",
    "olpn",
    "TESTSIGMA_API_KEY",
    "password=",
)

#: Forbidden in a fixture, legitimate elsewhere. A tenant hostname is the
#: vendor's own and belongs in `plugin.json` and in prose that tells an operator
#: where to attach; inside a fixture the same string means someone pasted a real
#: tenant's data in. The distinction is the directory, so these two lists cannot
#: be merged however similar they look.
FORBIDDEN_IN_A_FIXTURE = FORBIDDEN_ANYWHERE + (
    "testsigma.com",
    "@gmail",
)


def _fixture_text(path):
    """A fixture's readable content, decompressing a `.tsu` export.

    A `.tsu` is gzipped JSON. Skipping it left the one fixture closest in shape
    to real customer export data unscanned by this check, so its content was
    clean only because nobody had edited it.
    """
    if path.suffix == ".tsu":
        import gzip

        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    return path.read_text(encoding="utf-8", errors="replace")


def test_the_compressed_fixture_is_actually_scanned():
    # Arms the check below: if decompression stops working, the .tsu would read
    # as empty and pass everything.
    export = FIXTURES_DIR / "tosca-subset-export" / "example.tsu"
    assert "Entities" in _fixture_text(export), "the .tsu did not decompress"


#: Directories that are never scanned. Caches hold copies of scanned sources, and
#: `.git` holds every version of them, so both would report faults already fixed.
_UNSCANNED = {"__pycache__", ".pytest_cache", ".git", "results"}


def _published_files():
    """Every file this plugin publishes, cache and history excluded."""
    for path in PLUGIN_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if _UNSCANNED & set(path.parts):
            continue
        yield path


def test_the_scan_reaches_beyond_fixtures():
    """Arms the check below.

    The previous scan covered fixtures only, and a customer system name sat in
    `references/authoring.md` the whole time. If the walk ever narrows back to
    fixtures, this fails rather than the leak check quietly passing again.
    """
    scanned = {p for p in _published_files()}
    assert any(p.parent.name == "references" for p in scanned)
    assert any(p.parent.name == "adapters" for p in scanned)
    assert any("skills" in p.parts for p in scanned)


@pytest.mark.parametrize("forbidden", FORBIDDEN_ANYWHERE)
def test_no_published_file_carries_client_data(forbidden):
    needle = forbidden.lower()
    for path in _published_files():
        # This file names every forbidden token by definition.
        if path.name == "test_evals.py":
            continue
        text = _fixture_text(path).lower()
        assert needle not in text, f"{path} contains {forbidden!r}"


@pytest.mark.parametrize("forbidden", FORBIDDEN_IN_A_FIXTURE)
def test_no_fixture_carries_third_party_or_client_data(forbidden):
    roots = [FIXTURES_DIR, EVALS_DIR / "fixtures"]
    needle = forbidden.lower()
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            assert needle not in _fixture_text(path).lower(), (
                f"{path} contains {forbidden!r}"
            )
