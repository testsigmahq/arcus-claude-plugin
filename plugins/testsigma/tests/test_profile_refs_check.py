"""A test's `param` references must resolve in the profile it declares.

`validate` pools every profile's columns and checks the pool, so a test bound to
one profile may reference another's column and compile. At run time nothing
substitutes, the step reads the marker as literal text, and the test passes
having checked nothing.

Verified against the live CLI before this was written:

    param.notInAnyProfile   TSF2021 refused   (so the check is live)
    param.onlyInB           accepted          (from a test bound to ProfileA)

The refusal is what makes the acceptance evidence rather than an absent check —
the arming discipline that two separate false conclusions today were missing.
"""

import subprocess
import sys
import textwrap

from support import PLUGIN_ROOT

SCRIPT = PLUGIN_ROOT / "scripts" / "check_profile_refs.py"

TDPS = {
    "A": 'tdp "ProfileA" {\n  column("onlyInA")\n\n  set "I" {\n    onlyInA = "a"\n  }\n}\n',
    "B": 'tdp "ProfileB" {\n  column("onlyInB")\n\n  set "I" {\n    onlyInB = "b"\n  }\n}\n',
}


def build(tmp_path, test_body):
    v = tmp_path / "tests" / "testsigma" / "p" / "a" / "v1"
    (v / "tdps" / "f").mkdir(parents=True)
    (v / "tests" / "f").mkdir(parents=True)
    for key, text in TDPS.items():
        (v / "tdps" / "f" / f"{key}.tdp.sigma").write_text(text, encoding="utf-8")
    (v / "tests" / "f" / "t.test.sigma").write_text(
        textwrap.dedent(test_body), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path / "tests" / "testsigma")],
        capture_output=True, text=True)


def test_a_reference_to_the_bound_profiles_column_passes(tmp_path):
    r = build(tmp_path, '''\
        test "t" {
          profile = tdp["ProfileA"].set("I")
          storeValue(param.onlyInA, "x")
        }
        ''')
    assert r.returncode == 0, r.stdout


def test_a_reference_to_another_profiles_column_is_refused(tmp_path):
    """The case `validate` accepts. This is the whole point of the script."""
    r = build(tmp_path, '''\
        test "t" {
          profile = tdp["ProfileA"].set("I")
          storeValue(param.onlyInB, "x")
        }
        ''')
    assert r.returncode == 1, r.stdout
    assert "onlyInB" in r.stdout
    assert "having checked nothing" in r.stdout


def test_the_bracket_form_is_caught_too(tmp_path):
    # Two spellings reach the same slot; catching one would be worse than
    # catching neither, because it would read as coverage.
    r = build(tmp_path, '''\
        test "t" {
          profile = tdp["ProfileA"].set("I")
          storeValue(param["onlyInB"], "x")
        }
        ''')
    assert r.returncode == 1, r.stdout


def test_a_test_declaring_no_profile_is_skipped(tmp_path):
    """Unbound `param` is the norm, not an edge case.

    The profile arrives from a suite or plan at run time. Refusing it would
    flag most of a healthy workspace, which is how a check gets disabled.
    """
    r = build(tmp_path, '''\
        test "t" {
          storeValue(param.onlyInB, "x")
        }
        ''')
    assert r.returncode == 0, r.stdout
    assert "skipped (no profile declared): 1" in r.stdout


def test_a_profile_the_workspace_does_not_hold_is_reported(tmp_path):
    r = build(tmp_path, '''\
        test "t" {
          profile = tdp["ProfileMissing"].set("I")
          storeValue(param.onlyInA, "x")
        }
        ''')
    assert r.returncode == 1, r.stdout
    assert "not in this workspace" in r.stdout


def test_the_group_scope_limit_is_stated_as_correctness(tmp_path):
    """Why a group's body is out of scope, written where the rule lives.

    A `stepGroup` carries its own `profile` attribute — verified against the
    build with `list blocks --kind stepGroup` — so its references resolve
    against that and not the calling test's, and `override(…)` replaces a value
    at the call site. Checking a group's body against the caller's profile would
    report faults that are not faults.

    Asserted because the first draft called it caution pending investigation.
    That framing invites a later reader to "finish the job" and widen the scope,
    which would make the check wrong rather than more complete.
    """
    # Normalised: the phrase spans a line wrap in the docstring, and a raw
    # substring check fails on it. Third time today a wrapped phrase defeated a
    # naive assertion.
    text = " ".join(SCRIPT.read_text(encoding="utf-8").split())
    assert "correctness rather than caution" in text
    assert "own `profile` attribute" in text
    assert "override" in text
