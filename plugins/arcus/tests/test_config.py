import json
import os
from pathlib import Path

import pytest

from auth import config


def test_plugin_data_dir_uses_cache_marketplace(monkeypatch, tmp_path):
    fake_root = tmp_path / "plugins" / "cache" / "Testsigma" / "arcus" / "0.1.0"
    fake_root.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(fake_root))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert config.plugin_data_dir() == str(tmp_path / "plugins" / "data" / "arcus-Testsigma")


def test_plugin_data_dir_inline_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert config.plugin_data_dir() == str(tmp_path / "plugins" / "data" / "arcus-inline")


def test_read_write_config_atomic(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    cfg = {
        "schema_version": 1,
        "api_server": "https://x",
        "auth_server": "https://y",
        "uuid": "abc",
        "account_id": "acc",
        "user_id": "u",
        "user_email": "e@x",
        "expires_at": "2026-01-01T00:00:00Z",
        "auth_status": "ok",
    }
    config.write_config(cfg)
    assert config.read_config() == cfg

    path = Path(config.config_path())
    assert oct(path.stat().st_mode)[-3:] == "600"


def test_read_config_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    assert config.read_config() is None


def test_load_plugin_hosts(tmp_path, monkeypatch):
    plugin_root = tmp_path / "plugins" / "arcus"
    plugin_root.mkdir(parents=True)
    (plugin_root / "servers.json").write_text(json.dumps({
        "apiServer": "https://staging.testsigma.com",
        "authServer": "https://staging.testsigma.com",
    }))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    hosts = config.load_plugin_hosts()
    assert hosts == {
        "apiServer": "https://staging.testsigma.com",
        "authServer": "https://staging.testsigma.com",
    }


def test_load_plugin_hosts_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    assert config.load_plugin_hosts() == {}
