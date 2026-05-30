"""Wraps GET /desktop/v1/<uuid>/refresh on chitragupt."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def refresh_tokens(host: str, uuid: str, refresh_token: str, timeout: float = 10.0) -> dict[str, Any] | None:
    """Return the new token pair on success; None on auth failure or network error."""
    qs = urlencode({"refresh_token": refresh_token})
    url = f"{host.rstrip('/')}/desktop/v1/{uuid}/refresh?{qs}"
    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError:
        return None
    except (URLError, OSError, json.JSONDecodeError):
        return None
    pair = data.get("data") or data
    if not isinstance(pair, dict) or not pair.get("access_token") or not pair.get("refresh_token"):
        return None
    return pair
