import json
import os
from pathlib import Path

import pytest

from auth import config


def test_plugin_data_dir_uses_cache_marketplace(monkeypatch, tmp_path):
    fake_root = tmp_path / "plugins" / "cache" / "Testsigma" / "atto" / "0.1.0"
    fake_root.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(fake_root))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert config.plugin_data_dir() == str(tmp_path / "plugins" / "data" / "atto-Testsigma")


def test_plugin_data_dir_inline_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert config.plugin_data_dir() == str(tmp_path / "plugins" / "data" / "atto-inline")


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


def test_load_marketplace_hosts(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    (repo_root / ".claude-plugin").mkdir(parents=True)
    (repo_root / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
        "name": "Testsigma",
        "plugins": [{
            "name": "atto",
            "config": {
                "apiServer": "https://staging.testsigma.com",
                "authServer": "https://staging.testsigma.com",
            },
        }],
    }))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(repo_root / "plugins" / "atto"))
    hosts = config.load_marketplace_hosts()
    assert hosts == {
        "apiServer": "https://staging.testsigma.com",
        "authServer": "https://staging.testsigma.com",
    }


def test_load_marketplace_hosts_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    assert config.load_marketplace_hosts() == {}
