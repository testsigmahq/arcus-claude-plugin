# plugins/arcus/tests/test_testsigma_tests_skill.py
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "testsigma-tests" / "SKILL.md"


def _frontmatter(text):
    # Parse a leading --- ... --- block into a dict without pyyaml.
    assert text.startswith("---\n"), "missing frontmatter"
    _, fm, _body = text.split("---\n", 2)
    out = {}
    for line in fm.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def test_skill_exists_with_name_and_triggering_description():
    assert SKILL.exists(), f"{SKILL} missing"
    fm = _frontmatter(SKILL.read_text())
    assert fm.get("name") == "testsigma-tests"
    desc = fm.get("description", "").lower()
    # The description is what Claude matches against natural-language requests.
    assert "test" in desc and "testsigma" in desc
    assert "e2e" in desc or "end-to-end" in desc


def test_skill_body_covers_the_procedure():
    body = SKILL.read_text().lower()
    # Detect type, pull reference from the CLI, author, validate offline, offer to run.
    assert "testsigma code reference" in body
    assert "testsigma code examples" in body
    assert "testsigma code validate" in body
    assert "testsigma code run" in body
    assert "testsigma list devices --local" in body
    # The safety gate: validate always; run only after confirmation.
    assert "run it now" in body or "explicit confirmation" in body
    # Placement convention.
    assert "tests/testsigma" in body
    # The three application types.
    for t in ("web", "mobile", "api"):
        assert t in body
    # CLI-presence guard.
    assert "command -v testsigma" in body or "testsigma --version" in body
