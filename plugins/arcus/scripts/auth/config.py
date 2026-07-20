"""Config + marketplace metadata reader for the arcus plugin auth flow."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _claude_home() -> str:
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def plugin_data_dir() -> str:
    """Resolve the persistent data dir for this plugin install.

    When loaded from the cache (path contains `cache/<marketplace>/<plugin>/<ver>/...`),
    returns `<claude_home>/plugins/data/<plugin>-<marketplace>`. Otherwise falls back
    to `arcus-inline` for repo/dev installs.
    """
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    parts = plugin_root.rstrip("/").split("/")
    if len(parts) >= 4 and "cache" in parts:
        i = parts.index("cache")
        if i + 2 < len(parts):
            marketplace, plugin = parts[i + 1], parts[i + 2]
            return os.path.join(_claude_home(), "plugins", "data", f"{plugin}-{marketplace}")
    return os.path.join(_claude_home(), "plugins", "data", "arcus-inline")


def config_path() -> str:
    return os.path.join(plugin_data_dir(), "config.json")


def read_config() -> dict[str, Any] | None:
    path = config_path()
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_config(cfg: dict[str, Any]) -> None:
    """Atomic write with mode 0600."""
    data_dir = plugin_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".config-", dir=data_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.chmod(tmp, 0o600)
        os.rename(tmp, config_path())
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def delete_config() -> None:
    try:
        os.unlink(config_path())
    except FileNotFoundError:
        pass


def load_plugin_hosts() -> dict[str, str]:
    """Read the deployment servers shipped with the plugin (`servers.json`).

    Lives next to the plugin under ``$CLAUDE_PLUGIN_ROOT``, so it resolves the
    same way for cache installs and inline/dev installs.
    """
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        return {}
    try:
        with open(Path(plugin_root) / "servers.json", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str)}
