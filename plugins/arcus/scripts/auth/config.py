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
    parts = plugin_root.replace("\\", "/").rstrip("/").split("/")
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
        os.replace(tmp, config_path())
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


def _plugin_root() -> Path:
    """Plugin root from the environment, else derived from this file's location."""
    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if root:
        return Path(root)
    # scripts/auth/config.py -> plugin root is parent.parent.parent.
    return Path(__file__).resolve().parent.parent.parent


def plugin_version() -> str:
    """The plugin version, read from ``.claude-plugin/plugin.json``.

    That manifest is the single source of truth: Claude Code parses it before any
    of this code runs, so it is the one place the version cannot be computed.
    Everything else derives from it rather than keeping its own copy.
    """
    try:
        with open(_plugin_root() / ".claude-plugin" / "plugin.json", encoding="utf-8") as f:
            version = json.load(f).get("version")
    except (OSError, json.JSONDecodeError):
        return "unknown"
    return version if isinstance(version, str) and version else "unknown"


def load_regions() -> tuple[dict[str, dict[str, str]], str]:
    """Return ``(regions, default_region_key)`` from the shipped ``servers.json``.

    Lives next to the plugin under ``$CLAUDE_PLUGIN_ROOT``, so it resolves the
    same way for cache installs and inline/dev installs.
    """
    try:
        with open(_plugin_root() / "servers.json", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}, ""
    raw = data.get("regions")
    if not isinstance(raw, dict):
        return {}, ""
    regions = {
        key: value
        for key, value in raw.items()
        # Both hosts required: a half-configured entry would resolve to an
        # empty URL and fail only at the first request.
        if isinstance(value, dict) and isinstance(value.get("apiServer"), str) and isinstance(value.get("authServer"), str)
    }
    default = data.get("defaultRegion")
    if not isinstance(default, str) or default not in regions:
        default = ""
    return regions, default


def current_region() -> str | None:
    """The region this install is signed in to, or None if it never has been.

    Written by ``login`` and cleared by ``logout``, so it persists across
    sessions and survives token refresh.
    """
    cfg = read_config()
    region = cfg.get("region") if cfg else None
    return region if isinstance(region, str) and region else None


def region_choices() -> list[tuple[str, str]]:
    """``(key, label)`` for every configured region, for display in /arcus:login."""
    regions, _ = load_regions()
    return [(key, str(value.get("label") or key)) for key, value in regions.items()]


def resolve_region(name: str | None) -> tuple[str, str, str] | None:
    """Resolve a region key to ``(key, api_server, auth_server)``.

    An empty or missing *name* falls back to ``defaultRegion``. Returns None when
    the name is unknown or nothing is configured, so the caller can report the
    valid choices rather than silently authenticating against the wrong host.
    """
    regions, default = load_regions()
    if not regions:
        return None
    key = (name or "").strip().lower() or default
    region = regions.get(key)
    if not region:
        return None
    return key, region["apiServer"], region["authServer"]
