"""Refresh-token storage: env override > OS keychain > file fallback."""
from __future__ import annotations

import os
from pathlib import Path

from auth.config import plugin_data_dir

_SERVICE = "arcus"
_USERNAME = "refresh-token"

# Keyring is optional. If import or backend init fails, fall back to file.
try:
    import keyring as _kr  # type: ignore[import-not-found]
    _kr.get_keyring()  # ensure a backend is available
    _keyring = _kr
except Exception:  # noqa: BLE001 — broad on purpose; keyring backends are flaky
    _keyring = None


def _fallback_path() -> str:
    return os.path.join(plugin_data_dir(), "refresh.token")


def load_refresh_token() -> str | None:
    env = os.environ.get("ARCUS_REFRESH_TOKEN", "").strip()
    if env:
        return env
    if _keyring is not None:
        try:
            v = _keyring.get_password(_SERVICE, _USERNAME)
            if v:
                return v
        except Exception:  # noqa: BLE001
            pass
    try:
        with open(_fallback_path(), encoding="utf-8") as f:
            v = f.read().strip()
            return v or None
    except FileNotFoundError:
        return None


def save_refresh_token(token: str) -> None:
    if _keyring is not None:
        try:
            _keyring.set_password(_SERVICE, _USERNAME, token)
            return
        except Exception:  # noqa: BLE001
            pass
    path = _fallback_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(token)


def delete_refresh_token() -> None:
    if _keyring is not None:
        try:
            _keyring.delete_password(_SERVICE, _USERNAME)
        except Exception:  # noqa: BLE001
            pass
    try:
        os.unlink(_fallback_path())
    except FileNotFoundError:
        pass
