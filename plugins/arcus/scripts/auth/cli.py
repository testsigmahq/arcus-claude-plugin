"""argparse entry point for /arcus:login and /arcus:logout slash commands."""

from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path

# scripts/auth/cli.py -> plugin root is parent.parent.parent.
_plugin_root = Path(__file__).resolve().parent.parent.parent
os.environ.setdefault("CLAUDE_PLUGIN_ROOT", str(_plugin_root))
sys.path.insert(0, str(_plugin_root / "scripts"))

from auth.config import current_region, plugin_version, region_choices, resolve_region
from auth.login import login
from auth.logout import logout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arcus-auth")
    sub = parser.add_subparsers(dest="cmd", required=True)
    login_parser = sub.add_parser("login", help="Authenticate with Arcus via browser")
    login_parser.add_argument(
        "--region",
        default=os.environ.get("ARCUS_REGION"),
        help="Arcus region to authenticate against (US, IN, EU). Case-insensitive; defaults to US.",
    )
    sub.add_parser("regions", help="List the available regions")
    sub.add_parser("logout", help="Clear local credentials")
    args = parser.parse_args(argv)

    if args.cmd == "regions":
        signed_in = current_region()
        default = resolve_region(None)
        default_key = default[0] if default else None
        for key, label in region_choices():
            if key == signed_in:
                note = "signed in"
            elif key == default_key:
                note = "default"
            else:
                note = ""
            # Keys are stored lowercase but shown uppercase; input is case-insensitive.
            print(f"{key.upper()}\t{label}\t{note}")
        return 0
    if args.cmd == "login":
        return login(plugin_version=plugin_version(), hostname=socket.gethostname(), region=args.region)
    if args.cmd == "logout":
        return logout()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
