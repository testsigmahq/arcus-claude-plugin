import types

from auth import keystore

SERVICE = "arcus"
USERNAME = "refresh-token"


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv("ARCUS_REFRESH_TOKEN", "from-env")
    assert keystore.load_refresh_token() == "from-env"


def test_keyring_path(monkeypatch):
    monkeypatch.delenv("ARCUS_REFRESH_TOKEN", raising=False)
    fake_keyring = types.SimpleNamespace(
        get_password=lambda s, u: "from-keyring" if (s, u) == (SERVICE, USERNAME) else None,
        set_password=lambda *a, **k: None,
        delete_password=lambda *a, **k: None,
    )
    monkeypatch.setattr(keystore, "_keyring", fake_keyring)
    assert keystore.load_refresh_token() == "from-keyring"


def test_file_fallback_when_keyring_unavailable(monkeypatch, tmp_path):
    monkeypatch.delenv("ARCUS_REFRESH_TOKEN", raising=False)
    monkeypatch.setattr(keystore, "_keyring", None)
    monkeypatch.setattr(keystore, "_fallback_path", lambda: str(tmp_path / "refresh.token"))

    keystore.save_refresh_token("file-fallback-value")
    assert keystore.load_refresh_token() == "file-fallback-value"

    path = tmp_path / "refresh.token"
    assert oct(path.stat().st_mode)[-3:] == "600"


def test_save_routes_to_keyring_when_available(monkeypatch):
    calls = []
    fake_keyring = types.SimpleNamespace(
        get_password=lambda s, u: None,
        set_password=lambda s, u, p: calls.append((s, u, p)),
        delete_password=lambda *a, **k: None,
    )
    monkeypatch.setattr(keystore, "_keyring", fake_keyring)
    keystore.save_refresh_token("v1")
    assert calls == [(SERVICE, USERNAME, "v1")]


def test_delete_clears_both_keyring_and_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ARCUS_REFRESH_TOKEN", raising=False)
    deleted = []
    fake_keyring = types.SimpleNamespace(
        get_password=lambda s, u: None,
        set_password=lambda *a, **k: None,
        delete_password=lambda s, u: deleted.append((s, u)),
    )
    monkeypatch.setattr(keystore, "_keyring", fake_keyring)
    fpath = tmp_path / "refresh.token"
    fpath.write_text("x")
    monkeypatch.setattr(keystore, "_fallback_path", lambda: str(fpath))

    keystore.delete_refresh_token()
    assert deleted == [(SERVICE, USERNAME)]
    assert not fpath.exists()


def test_acl_locks_file_to_owner_on_windows(monkeypatch, tmp_path):
    """Windows gets an explicit owner-only ACL; 0o600 alone is not enough there."""
    calls = []
    monkeypatch.setattr(keystore.os, "name", "nt")
    monkeypatch.setenv("USERNAME", "tester")
    monkeypatch.setattr(keystore.subprocess, "run", lambda cmd, **kw: calls.append(cmd))

    keystore._restrict_windows_acl(str(tmp_path / "refresh.token"))

    assert calls and calls[0][0] == "icacls"
    assert calls[0][-2:] == ["/grant:r", "tester:F"]


def test_acl_is_a_noop_off_windows(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(keystore.os, "name", "posix")
    monkeypatch.setattr(keystore.subprocess, "run", lambda cmd, **kw: calls.append(cmd))

    keystore._restrict_windows_acl(str(tmp_path / "refresh.token"))

    assert calls == []


def test_save_applies_acl(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(keystore, "_keyring", None)
    monkeypatch.setattr(keystore, "_fallback_path", lambda: str(tmp_path / "refresh.token"))
    monkeypatch.setattr(keystore, "_restrict_windows_acl", lambda p: seen.append(p))

    keystore.save_refresh_token("secret")

    assert seen == [str(tmp_path / "refresh.token")]
