from unittest.mock import MagicMock

from auth import config as config_mod
from auth import login as login_mod


def test_login_writes_config_after_successful_exchange(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.setattr(
        login_mod,
        "resolve_region",
        lambda name: ("us", "https://ts.example", "https://cg.example"),
    )

    listener = MagicMock()
    listener.address.return_value = ("127.0.0.1", 59123)
    listener.wait_for_result.return_value = {"code": "the-code", "state": "the-state"}
    monkeypatch.setattr(login_mod, "LoopbackListener", lambda **kw: listener)

    monkeypatch.setattr(login_mod, "secrets_token_urlsafe", lambda n: "the-state")
    monkeypatch.setattr(login_mod, "uuid_4", lambda: "the-uuid")
    monkeypatch.setattr(login_mod, "open_browser", lambda url: None)
    monkeypatch.setattr(
        login_mod,
        "exchange_code",
        lambda host, uuid, code: {
            "access_token": "a",
            "refresh_token": "r",
            "expires_in": 86400,
            "token_type": "Bearer",
        },
    )
    monkeypatch.setattr(
        login_mod,
        "decode_jwt_claims",
        lambda t: {
            "account_id": "acc",
            "user_id": "u",
            "email": "e@x",
        },
    )
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


def _run_login(monkeypatch, region):
    """Drive login() end to end with the browser and token exchange stubbed."""
    monkeypatch.setattr(login_mod, "open_browser", lambda url: None)

    listener = MagicMock()
    listener.address.return_value = ("127.0.0.1", 59123)
    listener.wait_for_result.return_value = {"code": "abc", "state": "xyz"}
    monkeypatch.setattr(login_mod, "LoopbackListener", lambda **kw: listener)
    monkeypatch.setattr(login_mod, "save_refresh_token", lambda token: None)
    monkeypatch.setattr(
        login_mod,
        "exchange_code",
        lambda *a, **k: {"access_token": "a.b.c", "refresh_token": "r", "expires_in": 3600},
    )
    monkeypatch.setattr(
        login_mod,
        "decode_jwt_claims",
        lambda token: {"account_id": "acct-1", "user_id": "user-1", "email": "dev@example.com"},
    )
    assert login_mod.login(plugin_version="0.1.0", hostname="laptop", region=region) == 0


def test_login_defaults_to_the_us_region(monkeypatch, tmp_path):
    """No --region means us; the picker in /arcus:login offers it as the default."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _run_login(monkeypatch, region=None)
    cfg = config_mod.read_config()
    assert cfg["region"] == "us"
    assert cfg["api_server"] == "https://agentic-test.testsigma.com"
    assert cfg["auth_server"] == "https://arcus.testsigma.com"


def test_login_uses_the_requested_region(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _run_login(monkeypatch, region="eu")
    cfg = config_mod.read_config()
    assert cfg["region"] == "eu"
    assert cfg["api_server"] == "https://agentic-test-eu.testsigma.com"
    assert cfg["auth_server"] == "https://arcus-eu.testsigma.com"


def test_login_region_is_case_insensitive(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _run_login(monkeypatch, region="IN")
    assert config_mod.read_config()["region"] == "in"


def test_login_refuses_an_unknown_region(monkeypatch, tmp_path, capsys):
    """Never fall back to a default host: that would authenticate the user
    against a region they did not ask for."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(login_mod, "open_browser", lambda url: None)

    rc = login_mod.login(plugin_version="0.1.0", hostname="laptop", region="atlantis")

    assert rc == 1
    assert config_mod.read_config() is None
    err = capsys.readouterr().err
    assert "atlantis" in err and "US (United States)" in err


def test_every_shipped_region_resolves_to_both_hosts():
    """A half-configured region would resolve to an empty URL and fail late."""
    regions, default = config_mod.load_regions()
    assert set(regions) == {"us", "in", "eu"}
    assert default == "us"
    for key in regions:
        resolved = config_mod.resolve_region(key)
        assert resolved is not None
        _key, api, auth = resolved
        assert api.startswith("https://") and auth.startswith("https://")


def _seed_config(region):
    """Pretend this machine already signed in to *region*."""
    config_mod.write_config(
        {
            "schema_version": 1,
            "region": region,
            "api_server": "https://old-api.example",
            "auth_server": "https://old-auth.example",
            "auth_status": "ok",
        }
    )


def test_relogin_keeps_the_stored_region(monkeypatch, tmp_path):
    """An expired token must not silently relocate the user to the default."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _seed_config("eu")

    _run_login(monkeypatch, region=None)

    cfg = config_mod.read_config()
    assert cfg["region"] == "eu"
    assert cfg["auth_server"] == "https://arcus-eu.testsigma.com"


def test_explicit_region_switches_and_warns(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _seed_config("eu")

    _run_login(monkeypatch, region="in")

    assert config_mod.read_config()["region"] == "in"
    assert "switching region EU -> IN" in capsys.readouterr().err


def test_logout_forgets_the_region(monkeypatch, tmp_path):
    """After logout the next login is a first login again."""
    from auth import logout as logout_mod

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _seed_config("eu")
    assert config_mod.current_region() == "eu"

    monkeypatch.setattr(logout_mod, "delete_refresh_token", lambda: None)
    logout_mod.logout()

    assert config_mod.current_region() is None
    _run_login(monkeypatch, region=None)
    assert config_mod.read_config()["region"] == "us"


def test_stored_region_that_no_longer_exists_falls_back(monkeypatch, tmp_path, capsys):
    """A retired region must not lock someone out of signing in."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _seed_config("antarctica")

    _run_login(monkeypatch, region=None)

    assert config_mod.read_config()["region"] == "us"
    assert "no longer available" in capsys.readouterr().err
