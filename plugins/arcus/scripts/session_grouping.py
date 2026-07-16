"""
Derive TestSigma-oriented grouping keys for session_manifest.json.

Signals (best-effort from hook payloads):
  - Git branch name -> ticket IDs via regex (e.g. feature/PROJ-123-auth)
  - ``git_branch`` + cumulative ``git_branches_union`` (hook fields + Bash tool I/O)
  - Proactive ``git rev-parse --abbrev-ref HEAD`` on SessionStart (+ periodic refresh)
  - Every user prompt (UserPromptSubmit) -> ticket IDs merged cumulatively (not only the first message)

Server-side can merge with PR data, commits, etc. This is client-side signal only.
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any

# --- Regexes ----------------------------------------------------------------

_TICKET = re.compile(r"\b([A-Za-z][A-Za-z0-9]+-\d+)\b")
_RE_GIT_CHECKOUT_B = re.compile(r"\bgit\s+checkout\s+-b\s+(\S+)", re.I)
_RE_GIT_CHECKOUT = re.compile(r"\bgit\s+checkout\s+(?!-)([^\s;|&]+)", re.I)
_RE_GIT_SWITCH_C = re.compile(r"\bgit\s+switch\s+(?:-c|--create)\s+(\S+)", re.I)
_RE_GIT_SWITCH = re.compile(r"\bgit\s+switch\s+(?!-c\b)(?!-)(\S+)", re.I)
_RE_GIT_STDOUT_SWITCHED = re.compile(
    r"Switched to a new branch\s+['\"]([^'\"]+)['\"]|"
    r"Switched to branch\s+['\"]([^'\"]+)['\"]",
    re.I,
)
_RE_GIT_DASH_C_QUOTED = re.compile(r'^git\s+-C\s+"([^"]+)"\s*', re.I)
_RE_GIT_DASH_C = re.compile(r"^git\s+-C\s+(\S+)\s*", re.I)

_BRANCH_KEYS = ("git_branch", "gitBranch", "branch", "git_ref")

# Caps for union lists in grouping_keys — long sessions could otherwise grow unbounded.
_MAX_BRANCHES_UNION = 200
_MAX_TICKETS_UNION = 500


# --- Small generic helpers --------------------------------------------------


def _nonempty_str(v: Any) -> str | None:
    """Return stripped string if v is a non-empty str, else None."""
    return v.strip() if isinstance(v, str) and v.strip() else None


def _ensure_list(d: dict[str, Any], key: str) -> list[Any]:
    """Return d[key] as a list, initializing it in place if missing or wrong type."""
    if not isinstance(v := d.get(key), list):
        v = []
        d[key] = v
    return v


def _collect_branches(text: str, regexes: tuple[re.Pattern[str], ...]) -> list[str]:
    """Run each regex on text and return normalized branch names from all groups."""
    out: list[str] = []
    for rx in regexes:
        for m in rx.finditer(text):
            for g in m.groups():
                if g and not g.startswith("-") and (nb := _normalize_branch_name(g)):
                    out.append(nb)
    return out


# --- Ticket / branch primitives ---------------------------------------------


def _extract_ticket_ids(text: str) -> list[str]:
    """Return unique ticket keys (uppercased) in first-seen order."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _TICKET.finditer(text or ""):
        key = m.group(1).upper()
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def _union_unique(*lists: list[str]) -> list[str]:
    """Concatenate lists, deduped, preserving first-seen order."""
    seen: set[str] = set()
    out: list[str] = []
    for lst in lists:
        for x in lst:
            if x not in seen:
                seen.add(x)
                out.append(x)
    return out


def _pick_git_branch(payload: dict[str, Any]) -> str | None:
    """Return first non-empty branch value from payload or its metadata dict."""
    for src in (payload, payload.get("metadata")):
        if not isinstance(src, dict):
            continue
        for k in _BRANCH_KEYS:
            if v := _nonempty_str(src.get(k)):
                return v
    return None


def _normalize_branch_name(name: str) -> str | None:
    """Strip ``refs/heads/`` and reject detached / placeholder branch names."""
    n = (name or "").strip()
    if not n or n.startswith("(") or "detached" in n.lower():
        return None
    if n.startswith("refs/heads/"):
        n = n[len("refs/heads/") :]
    return n or None


def _merge_branch_union(gk: dict[str, Any], branch: str | None, *, set_current: bool) -> None:
    """Append normalized branch to git_branches_union; optionally set git_branch."""
    b = _normalize_branch_name(branch or "")
    if not b:
        return
    u = _ensure_list(gk, "git_branches_union")
    if b not in u:
        if len(u) >= _MAX_BRANCHES_UNION:
            u.pop(0)
        u.append(b)
    if set_current:
        gk["git_branch"] = b


# --- Bash command parsing ---------------------------------------------------


def _collapse_git_dash_c(cmd: str) -> str:
    """Strip leading ``git -C <path>`` prefixes so subcommand regexes match."""
    s = cmd.strip()
    if not s.lower().startswith("git"):
        return s
    while m := (_RE_GIT_DASH_C_QUOTED.match(s) or _RE_GIT_DASH_C.match(s)):
        rest = s[m.end() :].lstrip()
        s = ("git " + rest) if rest else "git"
    return s


def _branches_from_git_command(collapsed_cmd: str) -> list[str]:
    """Extract branch names from a collapsed ``git checkout|switch`` command string."""
    if not collapsed_cmd or "git" not in collapsed_cmd.lower():
        return []
    return _collect_branches(
        collapsed_cmd,
        (_RE_GIT_CHECKOUT_B, _RE_GIT_SWITCH_C, _RE_GIT_CHECKOUT, _RE_GIT_SWITCH),
    )


def _branches_from_git_checkout_stdout(stdout: str) -> list[str]:
    """Extract branch names from ``Switched to ...`` lines in git stdout."""
    return _collect_branches(stdout or "", (_RE_GIT_STDOUT_SWITCHED,))


def _bash_stdout(tool_response: Any) -> str:
    """Return stdout-like string from a Bash tool_response (str or dict)."""
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        for k in ("stdout", "output", "text", "body"):
            if isinstance(v := tool_response.get(k), str):
                return v
    return ""


# --- Subprocess + URL helpers -----------------------------------------------


def _to_https_git_url(url: str) -> str:
    """Convert SSH / ssh:// / https remote URLs into ``https://...git`` form."""
    if m := re.match(r"^[\w.-]+@([\w.-]+):(.*?)(?:\.git)?$", url):
        return f"https://{m.group(1)}/{m.group(2)}.git"
    if m := re.match(r"^ssh://[\w.-]+@([\w.-]+)/(.*?)(?:\.git)?$", url):
        return f"https://{m.group(1)}/{m.group(2)}.git"
    if url.startswith("https://"):
        return url if url.endswith(".git") else url + ".git"
    return url


def _run_cmd(cmd: list[str], cwd: str | None) -> str | None:
    """Run a shell command and return stripped stdout, or None on failure."""
    work_dir = (cwd or "").strip() or None
    if work_dir and not os.path.isdir(work_dir):
        work_dir = None
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5, cwd=work_dir,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _detect_git_repo(cwd: str | None) -> str | None:
    """Detect remote repo HTTPS URL via gh CLI, falling back to ``git remote``."""
    if (gh_url := _run_cmd(["gh", "repo", "view", "--json", "url", "-q", ".url"], cwd)) and gh_url.startswith("https://"):
        return gh_url if gh_url.endswith(".git") else gh_url + ".git"
    if url := _run_cmd(["git", "remote", "get-url", "origin"], cwd):
        return _to_https_git_url(url)
    return None


def _detect_git_branch(cwd: str | None) -> str | None:
    """Detect current branch via ``git rev-parse``, or None for detached HEAD."""
    branch = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    return None if branch == "HEAD" else branch


def _detect_git_user_email(cwd: str | None) -> str | None:
    """Detect git user email (``git config user.email``) or None."""
    return _run_cmd(["git", "config", "user.email"], cwd)


def _detect_git_user_name(cwd: str | None) -> str | None:
    """Detect git user name (``git config user.name``) or None."""
    return _run_cmd(["git", "config", "user.name"], cwd)


# --- Bash-driven branch ingestion -------------------------------------------


def _parse_git_branch_listing(stdout: str) -> tuple[str | None, list[str]]:
    """Parse ``git branch`` style output into (current_branch, all_branches)."""
    current: str | None = None
    names: list[str] = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line or line.startswith("("):
            continue
        is_current = line.startswith("*")
        if is_current:
            line = line[1:].strip()
        if not (nb := _normalize_branch_name(line.split("->", 1)[0].strip())):
            continue
        names.append(nb)
        if is_current:
            current = nb
    return current, names


def _ingest_git_branches_from_bash(
    gk: dict[str, Any], payload: dict[str, Any], hook_name: str
) -> None:
    """Update grouping keys from Bash tool_input/tool_response git commands."""
    tool_name = (payload.get("tool_name") or "").strip().lower()
    if tool_name != "bash":
        return
    if not isinstance(tool_input := payload.get("tool_input"), dict):
        return
    if not (cmd := _nonempty_str(tool_input.get("command"))):
        return
    collapsed = _collapse_git_dash_c(cmd)

    for b in _branches_from_git_command(collapsed):
        _merge_branch_union(gk, b, set_current=True)

    if hook_name != "PostToolUse":
        return

    stdout = _bash_stdout(payload.get("tool_response"))
    if not stdout.strip():
        return

    for b in _branches_from_git_checkout_stdout(stdout):
        _merge_branch_union(gk, b, set_current=True)

    if "rev-parse" in collapsed.lower() and "abbrev-ref" in collapsed.lower():
        lines = stdout.strip().splitlines()
        line = lines[0] if lines else ""
        if line and "fatal" not in line.lower():
            _merge_branch_union(gk, line, set_current=True)
        return

    if re.search(r"\bgit\s+branch\b", collapsed, re.I):
        cur, listed = _parse_git_branch_listing(stdout)
        for b in listed:
            _merge_branch_union(gk, b, set_current=False)
        if cur:
            _merge_branch_union(gk, cur, set_current=True)


# --- Ticket aggregation + entry point ---------------------------------------


def _merge_ticket_ids_into_union(gk: dict[str, Any], *texts: str | None) -> None:
    """Extract ticket IDs from each text and merge into gk['ticket_ids_union']."""
    new_ids: list[str] = []
    for t in texts:
        if t:
            new_ids.extend(_extract_ticket_ids(str(t)))
    if not new_ids:
        return
    existing = _ensure_list(gk, "ticket_ids_union")
    merged = _union_unique(existing, new_ids)
    if len(merged) > _MAX_TICKETS_UNION:
        merged = merged[-_MAX_TICKETS_UNION:]
    gk["ticket_ids_union"] = merged


def merge_grouping_into_manifest(
    manifest: dict[str, Any],
    payload: dict[str, Any],
    hook_name: str,
) -> None:
    """Mutate manifest in place, populating ``grouping_keys`` (idempotent)."""
    if not isinstance(gk := manifest.get("grouping_keys"), dict):
        gk = {}
        manifest["grouping_keys"] = gk

    cwd = payload.get("cwd") or manifest.get("cwd")
    refresh = hook_name == "SessionStart"

    # Branches: payload, then detection. Each source contributes ticket IDs.
    if branch := _pick_git_branch(payload):
        _merge_branch_union(gk, branch, set_current=True)
        _merge_ticket_ids_into_union(gk, branch)

    if refresh or not gk.get("git_branch"):
        if detected := _detect_git_branch(cwd):
            _merge_branch_union(gk, detected, set_current=True)
            _merge_ticket_ids_into_union(gk, detected)

    # Repo / user identity
    if refresh or not gk.get("git_repo"):
        if repo := _detect_git_repo(cwd):
            gk["git_repo"] = repo

    for key, detect in (
        ("git_user_email", _detect_git_user_email),
        ("git_user_name", _detect_git_user_name),
    ):
        if not gk.get(key) and (value := detect(cwd)):
            gk[key] = value

    # Bash side-channel can introduce more branches mid-session
    _ingest_git_branches_from_bash(gk, payload, hook_name)
    if cur_branch := gk.get("git_branch"):
        _merge_ticket_ids_into_union(gk, str(cur_branch))

    if hook_name == "UserPromptSubmit":
        if prompt := _nonempty_str(payload.get("prompt")):
            _merge_ticket_ids_into_union(gk, prompt)
