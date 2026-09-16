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

from auth.config import plugin_version
from auth.login import login
from auth.logout import logout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arcus-auth")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login", help="Authenticate with Testsigma via browser")
    sub.add_parser("logout", help="Clear local credentials")
    args = parser.parse_args(argv)

    if args.cmd == "login":
        return login(plugin_version=plugin_version(), hostname=socket.gethostname())
    if args.cmd == "logout":
        return logout()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
