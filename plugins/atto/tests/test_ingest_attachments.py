"""Tests for sensitive-path filtering in ingest_attachments."""

import pytest

import ingest_attachments


@pytest.mark.parametrize("path,expected", [
    (".env", True),
    ("/foo/.env", True),
    ("/foo/.env.local", True),
    ("/foo/.env.staging", True),
    ("/foo/.envrc", True),
    ("/foo/.netrc", True),
    ("/foo/.pgpass", True),
    ("/foo/credentials.json", True),
    ("/foo/secrets.yaml", True),
    ("/foo/service-account-prod.json", True),
    ("/foo/gcp_key.json", True),
    ("/home/user/.ssh/id_rsa", True),
    ("/home/user/.ssh/known_hosts", True),  # in .ssh dir
    ("/home/user/.aws/credentials", True),
    ("/foo/cert.pem", True),
    ("/foo/server.key", True),
    ("/foo/keystore.jks", True),
    # Should NOT match
    ("/foo/regular.py", False),
    ("/foo/README.md", False),
    ("/foo/id_rsa.pub", False),  # public key, not private
    ("/foo/main.py", False),
    ("/foo/EnvVariables.txt", False),  # not literally .env
])
def test_is_sensitive_path(path, expected):
    assert ingest_attachments._is_sensitive_path(path) is expected


def test_add_file_skips_sensitive(tmp_path):
    """build_ingest_attachments must mark sensitive files skipped."""
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=hunter2")
    sdir = str(tmp_path)
    record = {
        "hook_event_name": "PostToolUse",
        "payload": {
            "x": {"_externalized": True, "path": str(env_file)},
        },
    }
    result = ingest_attachments.build_ingest_attachments(sdir, record)
    sensitive = [r for r in result if r.get("relative_key", "").endswith(".env")]
    assert sensitive, "expected at least one entry for .env"
    assert all(r.get("skipped") and r.get("reason") == "sensitive_path" for r in sensitive)
    # No content_base64 field on skipped sensitive entries
    assert all("content_base64" not in r for r in sensitive)


def test_add_file_includes_normal_file(tmp_path):
    """Sanity: a regular file still gets attached."""
    f = tmp_path / "notes.md"
    f.write_text("hello")
    sdir = str(tmp_path)
    record = {
        "hook_event_name": "PostToolUse",
        "payload": {"x": {"_externalized": True, "path": str(f)}},
    }
    result = ingest_attachments.build_ingest_attachments(sdir, record)
    md = [r for r in result if r.get("relative_key", "").endswith(".md")]
    assert md
    assert "content_base64" in md[0]


def test_custom_sensitive_pattern_via_env(monkeypatch):
    monkeypatch.setenv("TESTSIGMA_SENSITIVE_PATTERNS", "environment.json,*.secret")
    assert ingest_attachments._is_sensitive_path("/foo/environment.json") is True
    assert ingest_attachments._is_sensitive_path("/foo/api.secret") is True
    assert ingest_attachments._is_sensitive_path("/foo/normal.py") is False


def test_custom_sensitive_pattern_empty_env(monkeypatch):
    monkeypatch.setenv("TESTSIGMA_SENSITIVE_PATTERNS", "")
    assert ingest_attachments._is_sensitive_path("/foo/environment.json") is False


def test_custom_sensitive_pattern_full_path_glob(monkeypatch):
    monkeypatch.setenv("TESTSIGMA_SENSITIVE_PATTERNS", "*config/prod.yaml")
    assert ingest_attachments._is_sensitive_path("/repo/config/prod.yaml") is True
