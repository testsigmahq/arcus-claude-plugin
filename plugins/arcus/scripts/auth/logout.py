"""Clears local plugin auth state. Server-side revoke not in scope."""
from __future__ import annotations

import sys

from auth.config import delete_config
from auth.keystore import delete_refresh_token


def logout() -> int:
    delete_refresh_token()
    delete_config()
    print("arcus: signed out.", file=sys.stderr)
    return 0
