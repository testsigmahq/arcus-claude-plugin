"""Tests for the host-OS primitives in ``scripts/hostos.py``.

The Windows-only branches are exercised by forcing ``hostos.WINDOWS``, so the
behaviour is verified on every platform CI runs on rather than only on Windows.
"""

import os
import subprocess
import sys

import hostos

# --- safe_component ---------------------------------------------------------


def test_safe_component_escapes_reserved_device_names():
    # Reserved with or without an extension; "nul.txt" is as reserved as "nul".
    for name in ("nul", "NUL", "con", "aux", "COM1", "lpt9", "nul.txt", "Con.json"):
        assert hostos.safe_component(name) != name
        assert hostos.safe_component(name).startswith("_")


def test_safe_component_leaves_ordinary_names_alone():
    for name in ("main.py", "README.md", "console.log", "communication.ts", "nullable.rs"):
        assert hostos.safe_component(name) == name


def test_safe_component_strips_trailing_dot_and_space():
    # Windows silently drops these, which would collide two distinct names.
    assert hostos.safe_component("report.") == "report"
    assert hostos.safe_component("draft ") == "draft"
    assert hostos.safe_component("...") == "part"
    assert hostos.safe_component("") == "part"


# --- long_path --------------------------------------------------------------


def test_long_path_is_a_noop_off_windows(monkeypatch):
    monkeypatch.setattr(hostos, "WINDOWS", False)
    assert hostos.long_path("/tmp/a/b") == "/tmp/a/b"


def test_long_path_prefixes_on_windows(monkeypatch):
    monkeypatch.setattr(hostos, "WINDOWS", True)
    monkeypatch.setattr(os.path, "abspath", lambda p: "C:\\Users\\dev\\deep")
    assert hostos.long_path("deep") == "\\\\?\\C:\\Users\\dev\\deep"


def test_long_path_handles_unc_and_is_idempotent(monkeypatch):
    monkeypatch.setattr(hostos, "WINDOWS", True)
    monkeypatch.setattr(os.path, "abspath", lambda p: "\\\\server\\share\\f")
    assert hostos.long_path("f") == "\\\\?\\UNC\\server\\share\\f"
    assert hostos.long_path("\\\\?\\C:\\x") == "\\\\?\\C:\\x"


# --- file_lock --------------------------------------------------------------


def test_file_lock_is_taken_and_uses_a_sidecar(tmp_path):
    target = tmp_path / "session_manifest.json"
    target.write_text("{}", encoding="utf-8")
    with hostos.file_lock(str(target)) as locked:
        assert locked is hostos.LOCKING_AVAILABLE
        # Never in the file being rewritten: Windows locks are mandatory.
        assert (tmp_path / "session_manifest.json.lock").exists()
    assert target.read_text(encoding="utf-8") == "{}"


def test_file_lock_creates_missing_parent_dirs(tmp_path):
    target = tmp_path / "nested" / "deeper" / "manifest.json"
    with hostos.file_lock(str(target)) as locked:
        assert locked is hostos.LOCKING_AVAILABLE
    assert target.parent.is_dir()


def test_file_lock_yields_false_rather_than_raising(tmp_path, monkeypatch):
    # An unwritable lock path must degrade, never break the hook.
    def boom(*_a, **_k):
        raise OSError("read-only")

    monkeypatch.setattr(os, "open", boom)
    with hostos.file_lock(str(tmp_path / "x")) as locked:
        assert locked is False


def _lock_probe(target: str) -> subprocess.Popen:
    """Spawn a child that takes the same lock and prints LOCKED when it gets it."""
    scripts = os.path.dirname(os.path.abspath(hostos.__file__))
    code = (
        f"import sys; sys.path.insert(0, {scripts!r}); import hostos\n"
        f"with hostos.file_lock({target!r}) as got:\n"
        f"    print('LOCKED' if got else 'BLOCKED', flush=True)\n"
    )
    return subprocess.Popen(
        [sys.executable, "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )


def test_file_lock_excludes_a_second_process(tmp_path):
    """The lock is real across processes, not merely within one interpreter."""
    if not hostos.LOCKING_AVAILABLE:
        return
    target = str(tmp_path / "m.json")

    with hostos.file_lock(target) as locked:
        assert locked is True
        child = _lock_probe(target)
        try:
            # Must not acquire while we hold it.
            out, _ = child.communicate(timeout=3)
            assert out.strip() != "LOCKED"
        except subprocess.TimeoutExpired:
            pass  # blocked, which is the point
        else:
            child = None

    if child is not None:
        # Released now, so the waiter gets through.
        out, _ = child.communicate(timeout=20)
        assert out.strip() == "LOCKED"


# --- run_text ---------------------------------------------------------------


def test_run_text_returns_stripped_stdout():
    assert hostos.run_text([sys.executable, "-c", "print('  hi  ')"]) == "hi"


def test_run_text_returns_none_on_nonzero_exit():
    assert hostos.run_text([sys.executable, "-c", "raise SystemExit(3)"]) is None


def test_run_text_returns_none_for_missing_executable():
    assert hostos.run_text(["definitely-not-a-real-binary-xyz"]) is None
    assert hostos.run_text([]) is None


def test_run_text_decodes_utf8_output():
    """git emits UTF-8 on every platform, including Windows, so we decode as UTF-8."""
    env_child = [
        sys.executable,
        "-c",
        "import sys; sys.stdout.buffer.write('café-brücke'.encode('utf-8'))",
    ]
    assert hostos.run_text(env_child) == "café-brücke"


def test_run_text_never_raises_on_undecodable_output():
    """``text=True`` would raise UnicodeDecodeError here and kill git detection."""
    child = [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'branch-\\xff\\xfe')"]
    out = hostos.run_text(child)
    assert out is not None and out.startswith("branch-")


def test_run_text_ignores_a_missing_cwd(tmp_path):
    assert hostos.run_text([sys.executable, "-c", "print(1)"], cwd=str(tmp_path / "nope")) == "1"


def test_run_text_survives_a_timeout():
    assert hostos.run_text([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.5) is None


# --- restrict_file ----------------------------------------------------------


def test_restrict_file_sets_owner_only_mode_on_posix(tmp_path, monkeypatch):
    monkeypatch.setattr(hostos, "WINDOWS", False)
    f = tmp_path / "refresh.token"
    f.write_text("secret", encoding="utf-8")
    hostos.restrict_file(str(f))
    if os.name != "nt":
        # Real Windows has no POSIX mode bits to assert on.
        assert oct(f.stat().st_mode)[-3:] == "600"


def test_restrict_file_grants_a_domain_qualified_acl_on_windows(tmp_path, monkeypatch):
    f = tmp_path / "refresh.token"
    f.write_text("secret", encoding="utf-8")
    seen = []
    monkeypatch.setattr(hostos, "WINDOWS", True)
    monkeypatch.setattr(hostos, "run_text", lambda cmd, **kw: seen.append(cmd))
    monkeypatch.setenv("USERNAME", "dev")
    monkeypatch.setenv("USERDOMAIN", "CORP")
    hostos.restrict_file(str(f))
    # Domain-qualified: a local and a domain account can share a bare name.
    assert seen and seen[0][0] == "icacls" and "CORP\\dev:F" in seen[0]


# --- version single-sourcing -------------------------------------------------


def test_pyproject_version_matches_the_plugin_manifest():
    """``plugin.json`` is the source of truth; nothing may carry a stale copy.

    Claude Code parses that manifest before any of this code runs, so its version
    has to be a literal. ``pyproject.toml`` needs a literal too (PEP 621, and this
    project declares no build backend that could compute one), so the duplicate is
    unavoidable — this test is what keeps it honest.
    """
    import json
    import re

    root = os.path.dirname(os.path.dirname(os.path.abspath(hostos.__file__)))
    with open(os.path.join(root, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        manifest_version = json.load(f)["version"]
    with open(os.path.join(root, "pyproject.toml"), encoding="utf-8") as f:
        pyproject_version = re.search(r'^version = "([^"]+)"', f.read(), re.M).group(1)

    assert pyproject_version == manifest_version, (
        f"pyproject.toml says {pyproject_version}, plugin.json says {manifest_version} — bump both in the same commit"
    )


def test_plugin_version_is_read_from_the_manifest(monkeypatch, tmp_path):
    """No hardcoded copy: the login flow reports whatever the manifest says."""
    from auth.config import plugin_version

    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text('{"version": "9.9.9"}', encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    assert plugin_version() == "9.9.9"


def test_plugin_version_degrades_when_the_manifest_is_unreadable(monkeypatch, tmp_path):
    from auth.config import plugin_version

    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / "gone"))
    assert plugin_version() == "unknown"
