"""argparse entry point for /atto:project slash commands."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# scripts/project/cli.py -> plugin root is parent.parent.parent.
_plugin_root = Path(__file__).resolve().parent.parent.parent
os.environ.setdefault("CLAUDE_PLUGIN_ROOT", str(_plugin_root))
sys.path.insert(0, str(_plugin_root / "scripts"))

from auth.config import read_config, write_config
from auth.state import AuthState
from project.api import list_projects, patch_workflow_project


def _cmd_list(args: argparse.Namespace) -> int:
    auth = AuthState.load()
    if not auth.usable():
        print("atto: not authenticated. Run /atto:login first.", file=sys.stderr)
        return 1
    projects = list_projects(auth, search=args.search)
    if projects is None:
        return 2
    if not projects:
        print("(no projects)")
        return 0
    id_w = max(max(len(str(p.get("id", ""))) for p in projects), len("ID"))
    pre_w = max(
        max((len(p.get("human_id_prefix") or "") for p in projects), default=0),
        len("PREFIX"),
    )
    print(f"Projects ({len(projects)}):")
    print(f"  {'ID'.ljust(id_w)}  {'PREFIX'.ljust(pre_w)}  NAME")
    for p in projects:
        pid = str(p.get("id", "")).ljust(id_w)
        prefix = (p.get("human_id_prefix") or "").ljust(pre_w)
        print(f"  {pid}  {prefix}  {p.get('name', '')}")
    return 0


def _cmd_use(args: argparse.Namespace) -> int:
    cfg = read_config()
    if not cfg:
        print("atto: not authenticated. Run /atto:login first.", file=sys.stderr)
        return 1
    auth = AuthState.load()
    cfg["project_id"] = args.project_id
    # Best-effort: resolve human id + name so `current` can show them offline.
    human_id = ""
    name = ""
    for p in list_projects(auth) or []:
        if str(p.get("id")) == str(args.project_id):
            human_id = p.get("human_id_prefix") or ""
            name = p.get("name") or ""
            break
    cfg["project_human_id"] = human_id
    cfg["project_name"] = name
    write_config(cfg)
    print("atto: pinned project")
    print(f"  project   {args.project_id}" + (f"  {human_id}" if human_id else ""))
    if name:
        print(f"  name      {name}")
    # Best-effort: update any active workflow attached to this session.
    workflow_id = cfg.get("active_workflow_id")
    if workflow_id:
        if patch_workflow_project(auth, workflow_id, args.project_id):
            print(f"  workflow  {workflow_id} (project updated)")
    return 0


def _cmd_current(_args: argparse.Namespace) -> int:
    cfg = read_config() or {}
    pid = cfg.get("project_id")
    if not pid:
        print("(no project pinned; run /atto:project use <id>)")
        return 0
    # Cache miss (e.g. project pinned before metadata caching existed): resolve
    # human id + name once via the API and backfill so future calls stay offline.
    if "project_human_id" not in cfg:
        auth = AuthState.load()
        if auth.usable():
            for p in list_projects(auth) or []:
                if str(p.get("id")) == str(pid):
                    cfg["project_human_id"] = p.get("human_id_prefix") or ""
                    cfg["project_name"] = p.get("name") or ""
                    write_config(cfg)
                    break
    human_id = cfg.get("project_human_id") or ""
    name = cfg.get("project_name") or ""
    print(f"project   {pid}" + (f"  {human_id}" if human_id else ""))
    if name:
        print(f"name      {name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atto-project")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List Testsigma projects")
    p_list.add_argument("search", nargs="?", default=None, help="Substring filter")
    p_list.set_defaults(func=_cmd_list)

    p_use = sub.add_parser("use", help="Pin active project for new events")
    p_use.add_argument("project_id")
    p_use.set_defaults(func=_cmd_use)

    p_cur = sub.add_parser("current", help="Print pinned project_id")
    p_cur.set_defaults(func=_cmd_current)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
