import json
import os
from pathlib import Path

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
    if os.name != "nt":
        # Windows has no POSIX mode bits; hostos.restrict_file sets an ACL instead.
        assert oct(path.stat().st_mode)[-3:] == "600"


def test_read_config_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    assert config.read_config() is None


def test_load_regions_reads_the_shipped_servers_file(tmp_path, monkeypatch):
    plugin_root = tmp_path / "plugins" / "arcus"
    plugin_root.mkdir(parents=True)
    (plugin_root / "servers.json").write_text(
        json.dumps(
            {
                "defaultRegion": "us",
                "regions": {
                    "us": {
                        "label": "United States",
                        "apiServer": "https://staging.testsigma.com",
                        "authServer": "https://staging-auth.testsigma.com",
                    }
                },
            }
        )
    )
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))

    regions, default = config.load_regions()
    assert default == "us"
    assert regions["us"]["apiServer"] == "https://staging.testsigma.com"
    assert config.resolve_region(None) == (
        "us",
        "https://staging.testsigma.com",
        "https://staging-auth.testsigma.com",
    )


def test_load_regions_drops_half_configured_entries(tmp_path, monkeypatch):
    """A region with only one host would resolve to an empty URL and fail late."""
    plugin_root = tmp_path / "plugins" / "arcus"
    plugin_root.mkdir(parents=True)
    (plugin_root / "servers.json").write_text(
        json.dumps(
            {
                "defaultRegion": "us",
                "regions": {
                    "us": {
                        "apiServer": "https://a.example",
                        "authServer": "https://b.example",
                    },
                    "broken": {"apiServer": "https://only-one.example"},
                },
            }
        )
    )
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))

    regions, _ = config.load_regions()
    assert set(regions) == {"us"}
    assert config.resolve_region("broken") is None


def test_load_regions_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
    assert config.load_regions() == ({}, "")
    assert config.resolve_region(None) is None
