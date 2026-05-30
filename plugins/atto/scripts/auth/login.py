"""Orchestrates the /atto:login flow."""
from __future__ import annotations

import base64
import json
import secrets
import sys
import uuid as _uuid
import webbrowser
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from auth.config import load_marketplace_hosts, write_config
from auth.keystore import save_refresh_token
from auth.listener import LoopbackListener


def secrets_token_urlsafe(n: int) -> str:
    return secrets.token_urlsafe(n)


def uuid_4() -> str:
    return str(_uuid.uuid4())


def open_browser(url: str) -> None:
    webbrowser.open(url)


def decode_jwt_claims(token: str) -> dict[str, Any]:
    """Best-effort decode of JWT body without signature verification."""
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    pad = "=" * ((4 - len(parts[1]) % 4) % 4)
    try:
        body = base64.urlsafe_b64decode(parts[1] + pad).decode("utf-8")
        return json.loads(body)
    except (ValueError, json.JSONDecodeError):
        return {}


def exchange_code(host: str, uuid: str, code: str, timeout: float = 10.0) -> dict[str, Any] | None:
    qs = urlencode({"code": code})
    url = f"{host.rstrip('/')}/desktop/v1/{uuid}/tokens?{qs}"
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = "<no body>"
        print(f"atto: token exchange HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except (URLError, OSError, json.JSONDecodeError) as e:
        print(f"atto: token exchange error: {type(e).__name__}: {e}", file=sys.stderr)
        return None
    if isinstance(data, dict) and data.get("access_token") and data.get("refresh_token"):
        return data
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        d = data["data"]
        if d.get("access_token") and d.get("refresh_token"):
            return d
    return None


def login(plugin_version: str, hostname: str) -> int:
    hosts = load_marketplace_hosts()
    api_server = hosts.get("apiServer", "")
    auth_server = hosts.get("authServer", "")
    if not api_server or not auth_server:
        print(
            "atto: marketplace.json missing apiServer / authServer. "
            "Reinstall the plugin from your Testsigma marketplace.",
            file=sys.stderr,
        )
        return 1

    uuid = uuid_4()
    state = secrets_token_urlsafe(32)
    listener = LoopbackListener(expected_state=state, timeout_seconds=300.0)
    listener.start()
    host_addr, port = listener.address()

    params = {
        "uuid": uuid,
        "type": "CLAUDE_PLUGIN",
        "state": state,
        "port": str(port),
        "v": plugin_version,
        "hostname": hostname,
    }
    auth_url = f"{auth_server.rstrip('/')}/ui/agentic/authorize?{urlencode(params)}"
    print(f"atto: opening browser to {auth_url}", file=sys.stderr)
    open_browser(auth_url)

    received = listener.wait_for_result()
    listener.stop()
    if received is None:
        print("atto: login timed out (5 min). Run /atto:login again.", file=sys.stderr)
        return 2

    code = received.get("code", "")
    if not code:
        print("atto: login response missing code.", file=sys.stderr)
        return 3

    pair = exchange_code(auth_server, uuid, code)
    if pair is None:
        print("atto: token exchange failed. Run /atto:login again.", file=sys.stderr)
        return 4

    save_refresh_token(pair["refresh_token"])

    claims = decode_jwt_claims(pair["access_token"])
    account_id = str(claims.get("account_id") or "").strip()
    user_id = str(claims.get("user_id") or "").strip()
    if not account_id or not user_id:
        print(
            "atto: access token missing required account_id / user_id claims. "
            "Run /atto:login again or contact support.",
            file=sys.stderr,
        )
        return 5

    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=int(pair.get("expires_in", 86400)))
    ).isoformat()

    write_config({
        "schema_version": 1,
        "api_server": api_server,
        "auth_server": auth_server,
        "uuid": uuid,
        "account_id": account_id,
        "user_id": user_id,
        "user_email": str(claims.get("email", "")),
        "expires_at": expires_at,
        "auth_status": "ok",
    })

    user_label = claims.get("email") or claims.get("user_id") or "(unknown)"
    print(f"atto: authenticated as {user_label}. You can close the browser tab.", file=sys.stderr)
    return 0
