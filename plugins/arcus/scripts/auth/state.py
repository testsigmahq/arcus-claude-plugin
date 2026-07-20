"""AuthState facade: reads config + refresh token, lazily refreshes access token."""
from __future__ import annotations

import fcntl
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from auth.config import plugin_data_dir, read_config, write_config
from auth.keystore import load_refresh_token, save_refresh_token
from auth.refresh import refresh_tokens


def _parse_iso(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


@contextmanager
def _refresh_lock():
    """Serialize refresh across concurrent processes."""
    data_dir = plugin_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "refresh.lock")
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


@dataclass
class AuthState:
    config: dict[str, Any] | None = None
    refresh_token_value: str | None = None

    @classmethod
    def load(cls) -> "AuthState":
        cfg = read_config()
        rtok = load_refresh_token() if cfg else None
        return cls(config=cfg, refresh_token_value=rtok)

    def usable(self) -> bool:
        if not self.config:
            return False
        if self.config.get("auth_status") != "ok":
            return False
        if not self.refresh_token_value:
            return False
        return True

    @property
    def api_server(self) -> str | None:
        return self.config.get("api_server") if self.config else None

    @property
    def auth_server(self) -> str | None:
        return self.config.get("auth_server") if self.config else None

    @property
    def uuid(self) -> str | None:
        return self.config.get("uuid") if self.config else None

    def _cached_access_token(self) -> str | None:
        if not self.config:
            return None
        tok = self.config.get("access_token")
        exp = _parse_iso(self.config.get("access_expires_at") or "")
        if not tok or not exp:
            return None
        if datetime.now(timezone.utc) >= exp - timedelta(seconds=60):
            return None
        return tok

    def access_token(self) -> str | None:
        if not self.usable():
            return None
        cached = self._cached_access_token()
        if cached:
            return cached

        with _refresh_lock():
            # Reread after lock — another process may have refreshed.
            cfg = read_config()
            if cfg:
                self.config = cfg
                self.refresh_token_value = load_refresh_token()
            if not self.usable():
                return None
            cached = self._cached_access_token()
            if cached:
                return cached

            pair = refresh_tokens(
                host=self.auth_server or "",
                uuid=self.uuid or "",
                refresh_token=self.refresh_token_value or "",
            )
            if pair is None:
                self.mark_unauthed()
                return None

            access = pair["access_token"]
            expires_in = int(pair.get("expires_in", 86400))
            new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            new_refresh = pair["refresh_token"]
            self.refresh_token_value = new_refresh
            save_refresh_token(new_refresh)

            if self.config is not None:
                self.config["access_token"] = access
                self.config["access_expires_at"] = new_expires_at.isoformat()
                self.config["expires_at"] = new_expires_at.isoformat()
                write_config(self.config)
            return access

    def mark_unauthed(self) -> None:
        if self.config is None:
            return
        self.config["auth_status"] = "revoked"
        self.config.pop("access_token", None)
        self.config.pop("access_expires_at", None)
        write_config(self.config)
