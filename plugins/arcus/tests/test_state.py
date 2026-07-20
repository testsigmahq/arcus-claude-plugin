from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from auth import state as state_mod
from auth import config as config_mod


def _now_iso(offset_seconds: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).strftime("%Y-%m-%dT%H:%M:%S+00:00")


@pytest.fixture
def authed_setup(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    config_mod.write_config({
        "schema_version": 1,
        "api_server": "https://ts.example",
        "auth_server": "https://cg.example",
        "uuid": "u1",
        "account_id": "a1",
        "user_id": "u",
        "user_email": "e@x",
        "expires_at": _now_iso(7200),
        "auth_status": "ok",
    })
    monkeypatch.setattr(state_mod, "load_refresh_token", lambda: "stored-refresh")
    return tmp_path


def test_load_unauthed_when_no_config(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    s = state_mod.AuthState.load()
    assert s.usable() is False
    assert s.api_server is None


def test_load_authed_returns_usable(authed_setup):
    s = state_mod.AuthState.load()
    assert s.usable() is True
    assert s.api_server == "https://ts.example"
    assert s.auth_server == "https://cg.example"


def test_access_token_uses_cached_when_fresh(authed_setup, monkeypatch):
    # Seed the cached token in config (where AuthState._cached_access_token reads from).
    cfg = config_mod.read_config()
    cfg["access_token"] = "cached-access"
    cfg["access_expires_at"] = _now_iso(300)
    config_mod.write_config(cfg)

    s = state_mod.AuthState.load()
    called = []
    monkeypatch.setattr(state_mod, "refresh_tokens",
                        lambda **kw: called.append(kw) or None)
    assert s.access_token() == "cached-access"
    assert called == []


def test_access_token_refreshes_when_near_expiry(authed_setup, monkeypatch):
    s = state_mod.AuthState.load()
    s._access_token = "old"
    s._access_expires_at = datetime.now(timezone.utc) + timedelta(seconds=10)

    monkeypatch.setattr(state_mod, "refresh_tokens", lambda **kw: {
        "access_token": "new-access",
        "refresh_token": "new-refresh",
        "expires_in": 86400,
        "token_type": "Bearer",
    })
    saved = []
    monkeypatch.setattr(state_mod, "save_refresh_token", lambda v: saved.append(v))

    tok = s.access_token()
    assert tok == "new-access"
    assert saved == ["new-refresh"]


def test_access_token_marks_revoked_on_refresh_failure(authed_setup, monkeypatch):
    s = state_mod.AuthState.load()
    s._access_token = None
    monkeypatch.setattr(state_mod, "refresh_tokens", lambda **kw: None)

    tok = s.access_token()
    assert tok is None
    cfg = config_mod.read_config()
    assert cfg["auth_status"] == "revoked"


def test_mark_unauthed_persists(authed_setup):
    s = state_mod.AuthState.load()
    s.mark_unauthed()
    cfg = config_mod.read_config()
    assert cfg["auth_status"] == "revoked"
