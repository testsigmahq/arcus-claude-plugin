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


def test_the_gate_is_documented_beside_the_cases(self=None):
    assert EVAL_README.is_file(), (
        "the next person needs to know why these do not run"
    )
    body = EVAL_README.read_text(encoding="utf-8")
    assert has_paragraph_with(body, "early access", "entitlement"), (
        "it must say the gate is an entitlement rather than a version"
    )
    # Positive, not an absent guard: the guard I first wrote ("enable it by
    # editing") matched the document's own "do not try to enable it by editing a
    # settings file", which is the correct instruction. That is the sixth time
    # an absent guard has rejected honest prose in this suite.
    assert has_paragraph_with(
        body, "no settings file", "server-side"
    ), "it must say the gate is server-side and no setting turns it on"


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

    def test_a_skill_grader_relies_on_the_documented_automatic_behaviour(self, case):
        # `--help` says graders marked with-only, "incl. `tool_used: Skill`",
        # are a plugin-fired indicator rather than part of the score. The YAML
        # key that marks one explicitly is NOT documented, so nothing here
        # invents one: a made-up key would either be ignored or rejected, and
        # both are worse than relying on the stated automatic behaviour.
        for grader in _graders(case):
            meta, _ = _frontmatter(grader)
            if meta.get("type") == "tool_used" and meta.get("tool") == "Skill":
                assert "with_only" not in meta and "withOnly" not in meta, (
                    "the with-only key is undocumented; do not invent one"
                )

    def test_every_path_it_points_at_exists(self, case):
        directories = ((_case_yaml(case).get("context") or {}).get("add_dirs")) or []
        assert directories, f"{case.name} copies no fixture into the run"
        for entry in directories:
            resolved = (case / entry).resolve()
            assert resolved.exists(), f"{entry} does not exist (resolved {resolved})"


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


#: Shapes that would mean a fixture came from a real suite rather than being
#: hand-built. Checked because these fixtures are committed to a public
#: repository and the source material they imitate is a customer's.
FORBIDDEN_IN_A_FIXTURE = (
    "testsigma.com",
    "dhl",
    "@gmail",
    "TESTSIGMA_API_KEY",
    "password=",
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


@pytest.mark.parametrize("forbidden", FORBIDDEN_IN_A_FIXTURE)
def test_no_fixture_carries_third_party_or_client_data(forbidden):
    roots = [FIXTURES_DIR, EVALS_DIR / "fixtures"]
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            text = _fixture_text(path).lower()
            assert forbidden.lower() not in text, f"{path} contains {forbidden!r}"
