import os
import sys
import types

import pytest

from auth import keystore


SERVICE = "atto"
USERNAME = "refresh-token"


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv("ATTO_REFRESH_TOKEN", "from-env")
    assert keystore.load_refresh_token() == "from-env"


def test_keyring_path(monkeypatch):
    monkeypatch.delenv("ATTO_REFRESH_TOKEN", raising=False)
    fake_keyring = types.SimpleNamespace(
        get_password=lambda s, u: "from-keyring" if (s, u) == (SERVICE, USERNAME) else None,
        set_password=lambda *a, **k: None,
        delete_password=lambda *a, **k: None,
    )
    monkeypatch.setattr(keystore, "_keyring", fake_keyring)
    assert keystore.load_refresh_token() == "from-keyring"


def test_file_fallback_when_keyring_unavailable(monkeypatch, tmp_path):
    monkeypatch.delenv("ATTO_REFRESH_TOKEN", raising=False)
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
    monkeypatch.delenv("ATTO_REFRESH_TOKEN", raising=False)
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
