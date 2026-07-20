"""argparse entry point for /arcus:map slash commands."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# scripts/map/cli.py -> plugin root is parent.parent.parent.
_plugin_root = Path(__file__).resolve().parent.parent.parent
os.environ.setdefault("CLAUDE_PLUGIN_ROOT", str(_plugin_root))
sys.path.insert(0, str(_plugin_root / "scripts"))

from auth.config import plugin_data_dir
from auth.state import AuthState


def _latest_session_id() -> str | None:
    sessions = Path(plugin_data_dir()) / "sessions"
    if not sessions.is_dir():
        return None
    candidates = []
    for d in sessions.iterdir():
        manifest = d / "session_manifest.json"
        if manifest.is_file():
            candidates.append((manifest.stat().st_mtime, d.name))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _cmd_ticket(args: argparse.Namespace) -> int:
    auth = AuthState.load()
    if not auth.usable():
        print("arcus: not authenticated. Run /arcus:login first.", file=sys.stderr)
        return 1
    session_id = _latest_session_id()
    if not session_id:
        print("arcus: no session manifest yet. Trigger any tool call first.", file=sys.stderr)
        return 2
    host = (auth.api_server or "").rstrip("/")
    token = auth.access_token()
    if not host or not token:
        print("arcus: missing host or token.", file=sys.stderr)
        return 3
    body = json.dumps({"session_id": session_id, "ticket_key": args.ticket_key}).encode("utf-8")
    req = Request(
        f"{host}/api/v1/plugin/map/ticket",
        data=body,
        method="POST",
        headers={"x-agentic-token": token, "Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        msg = e.read().decode()[:300] if hasattr(e, "read") else str(e)
        print(f"arcus: map ticket failed ({e.code}): {msg}", file=sys.stderr)
        return 4
    except (URLError, OSError, json.JSONDecodeError) as e:
        print(f"arcus: map ticket error: {e}", file=sys.stderr)
        return 5

    wf = data.get("workflow_id")
    provider = data.get("provider") or "unknown"
    sprint = data.get("sprint_id")
    print("arcus: ticket mapped" if data.get("mapped") else "arcus: ticket already mapped")
    print(f"  ticket     {args.ticket_key} ({provider})")
    print(f"  workflow   {wf}")
    if sprint:
        print(f"  sprint     {sprint}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arcus-map")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ticket = sub.add_parser("ticket", help="Map ticket key to current session's workflow")
    p_ticket.add_argument("ticket_key")
    p_ticket.set_defaults(func=_cmd_ticket)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
