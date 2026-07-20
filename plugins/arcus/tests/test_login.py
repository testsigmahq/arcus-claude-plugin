import json
from unittest.mock import patch, MagicMock

import pytest

from auth import login as login_mod
from auth import config as config_mod


def test_login_writes_config_after_successful_exchange(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.setattr(login_mod, "load_plugin_hosts", lambda: {
        "apiServer": "https://ts.example",
        "authServer": "https://cg.example",
    })

    listener = MagicMock()
    listener.address.return_value = ("127.0.0.1", 59123)
    listener.wait_for_result.return_value = {"code": "the-code", "state": "the-state"}
    monkeypatch.setattr(login_mod, "LoopbackListener", lambda **kw: listener)

    monkeypatch.setattr(login_mod, "secrets_token_urlsafe", lambda n: "the-state")
    monkeypatch.setattr(login_mod, "uuid_4", lambda: "the-uuid")
    monkeypatch.setattr(login_mod, "open_browser", lambda url: None)
    monkeypatch.setattr(login_mod, "exchange_code", lambda host, uuid, code: {
        "access_token": "a", "refresh_token": "r",
        "expires_in": 86400, "token_type": "Bearer",
    })
    monkeypatch.setattr(login_mod, "decode_jwt_claims", lambda t: {
        "account_id": "acc", "user_id": "u", "email": "e@x",
    })
    saved = []
    monkeypatch.setattr(login_mod, "save_refresh_token", lambda v: saved.append(v))

    rc = login_mod.login(plugin_version="0.1.0", hostname="laptop")

    assert rc == 0
    assert saved == ["r"]
    cfg = config_mod.read_config()
    assert cfg["api_server"] == "https://ts.example"
    assert cfg["auth_server"] == "https://cg.example"
    assert cfg["uuid"] == "the-uuid"
    assert cfg["account_id"] == "acc"
    assert cfg["user_email"] == "e@x"
    assert cfg["auth_status"] == "ok"
