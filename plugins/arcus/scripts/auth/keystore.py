"""Refresh-token storage: env override > OS keychain > file fallback."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from auth.config import plugin_data_dir

_SERVICE = "arcus"
_USERNAME = "refresh-token"

# Keyring is optional. If import or backend init fails, fall back to file.
try:
    import keyring as _kr  # type: ignore[import-not-found]
    _kr.get_keyring()  # ensure a backend is available
    _keyring = _kr
except Exception:  # Broad on purpose: keyring backends are flaky.
    _keyring = None


def _restrict_windows_acl(path: str) -> None:
    """Owner-only ACL for the fallback token file.

    ``0o600`` only flips the read-only bit on Windows, so the plaintext refresh
    token would otherwise be readable by every account on the machine.
    """
    if os.name != "nt":
        return
    user = os.environ.get("USERNAME")
    if not user:
        return
    try:
        subprocess.run(
            ["icacls", path, "/inheritance:r", "/grant:r", f"{user}:F"],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass  # Best effort: the keyring backend is the primary store.


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
        except Exception:
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
        except Exception:
            pass
    path = _fallback_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(token)
    _restrict_windows_acl(path)


def delete_refresh_token() -> None:
    if _keyring is not None:
        try:
            _keyring.delete_password(_SERVICE, _USERNAME)
        except Exception:
            pass
    try:
        os.unlink(_fallback_path())
    except FileNotFoundError:
        pass
