"""
Per-session folder layout for captured chat/context artifacts.

sessions/<session_id>/
  session_manifest.json     — grouping + TestSigma link (ManifestSink); hook stream is POSTed to ingest API
  attachments/              — user-provided files referenced via @ in prompts
  context_files/            — snapshots from Claude's Read / Write / Edit tool calls (this module)
  context_files_index.jsonl — one JSON line per snapshot (metadata)

Disable snapshots: TESTSIGMA_DISABLE_CONTEXT_FILE_SNAPSHOTS=true
Max bytes per snapshot: TESTSIGMA_CONTEXT_FILE_MAX_BYTES (default 52428800 = 50 MiB)

Noise exclusion (dependency / build / VCS dirs are never snapshotted):
  TESTSIGMA_EXCLUDE_PATTERNS — comma-separated globs added to the built-in list
    (matched against basename, full path, and each path component).
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
from typing import Any

from capture_sinks import session_dir_for

_BAD_PATH = re.compile(r"[^\w\-.]+")

# Directory names that are dependency caches, build output, or VCS metadata —
# capturing files under them is noise, never the user's own work. Matched
# case-insensitively against every component of a path.
_DEFAULT_EXCLUDED_DIRS = frozenset({
    # JS / web
    "node_modules", "bower_components", "jspm_packages", ".pnp", ".yarn",
    ".next", ".nuxt", ".svelte-kit", ".angular", ".astro", ".expo", ".docusaurus",
    ".cache", ".parcel-cache", ".turbo", ".vite", ".webpack",
    # generic build output
    "dist", "build", "out", ".output", "coverage", ".nyc_output",
    # python
    ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".eggs",
    # jvm / go / php / rust
    "target", "vendor", ".gradle", ".mvn",
    # infra
    ".terraform", ".serverless",
    # ios / mac
    "pods", "carthage", "deriveddata",
    # vcs + editors
    ".git", ".hg", ".svn", ".idea", ".vscode",
})
# Component-level globs (e.g. compiled python package dirs).
_DEFAULT_EXCLUDED_DIR_GLOBS = ("*.egg-info",)


def _custom_exclude_patterns() -> list[str]:
    """Comma-separated globs from ``TESTSIGMA_EXCLUDE_PATTERNS`` (case-insensitive)."""
    raw = os.environ.get("TESTSIGMA_EXCLUDE_PATTERNS", "").strip()
    if not raw:
        return []
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def _is_excluded_path(path: str) -> bool:
    """True if *path* lives under a dependency/build/VCS dir (or matches a custom glob)."""
    if not path:
        return False
    norm = path.replace("\\", "/").lower()
    components = [c for c in norm.split("/") if c and c != "."]

    for c in components:
        if c in _DEFAULT_EXCLUDED_DIRS:
            return True
        if any(fnmatch.fnmatch(c, g) for g in _DEFAULT_EXCLUDED_DIR_GLOBS):
            return True

    base = os.path.basename(norm)
    for pat in _custom_exclude_patterns():
        if pat in components or fnmatch.fnmatch(base, pat) or fnmatch.fnmatch(norm, pat):
            return True

    return False


def _max_bytes() -> int:
    try:
        return int(os.environ.get("TESTSIGMA_CONTEXT_FILE_MAX_BYTES", str(50 * 1024 * 1024)))
    except ValueError:
        return 50 * 1024 * 1024


def _snapshots_disabled() -> bool:
    return os.environ.get("TESTSIGMA_DISABLE_CONTEXT_FILE_SNAPSHOTS", "").strip() in (
        "1",
        "true",
        "yes",
    )


def _safe_relative_storage_path(file_path: str, cwd: str) -> str:
    """Map absolute file_path to a safe path under context_files/."""
    try:
        fp = os.path.normpath(file_path)
        cw = os.path.normpath(cwd or "")
        if cw and (fp == cw or fp.startswith(cw + os.sep)):
            rel = os.path.relpath(fp, cw)
        else:
            rel = os.path.basename(fp) or "file"
        rel = rel.replace("\\", "/")
        parts: list[str] = []
        for p in rel.split("/"):
            if not p or p == ".":
                continue
            if p == "..":
                continue
            safe = _BAD_PATH.sub("_", p)
            if not safe:
                safe = "part"
            parts.append(safe)
        if not parts:
            parts = ["file"]
        return "/".join(parts)
    except Exception:
        h = hashlib.sha256(file_path.encode("utf-8", errors="replace")).hexdigest()[:16]
        return f"_path_{h}_{os.path.basename(file_path) or 'file'}"


def _extract_read_text(tool_response: Any) -> str | None:
    if tool_response is None:
        return None
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        for k in ("content", "stdout", "text", "body", "output"):
            v = tool_response.get(k)
            if isinstance(v, str):
                return v
        try:
            return json.dumps(tool_response, ensure_ascii=False, indent=2)
        except Exception:
            return str(tool_response)
    return str(tool_response)


def _append_index(session_dir: str, entry: dict[str, Any]) -> None:
    path = os.path.join(session_dir, "context_files_index.jsonl")
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


_AT_FILE_REF = re.compile(
    r"(?<!\S)@(~[/\\][^\s]+|/[^\s]+|\.\./[^\s]+|\./[^\s]+|[^\s@:]+/[^\s]+|[^\s@:]+\.\w+)"
)


def _strip_trailing_punct(s: str) -> str:
    return s.rstrip(".,;:!?)]}>\"'")


def _resolve_at_path(ref: str, cwd: str) -> str | None:
    """Resolve an @-reference to an absolute path, or *None* if it isn't a readable file."""
    path = os.path.expanduser(ref)
    if not os.path.isabs(path):
        path = os.path.join(cwd, path) if cwd else os.path.abspath(path)
    path = os.path.normpath(path)
    return path if os.path.isfile(path) else None


def persist_prompt_file_references(session_id: str, event_data: dict[str, Any]) -> int:
    """
    On ``UserPromptSubmit``, parse ``@``-file references from the prompt text,
    read each resolved file, and store it under ``attachments/`` (user-provided files).

    Returns the number of files successfully stored.
    """
    if _snapshots_disabled():
        return 0
    if event_data.get("hook_event_name") != "UserPromptSubmit":
        return 0

    prompt = event_data.get("prompt") or ""
    if not isinstance(prompt, str) or "@" not in prompt:
        return 0

    cwd = str(event_data.get("cwd") or "")
    raw_refs = _AT_FILE_REF.findall(prompt)
    if not raw_refs:
        return 0

    count = 0
    max_b = _max_bytes()
    session_dir = session_dir_for(session_id)
    base = os.path.join(session_dir, "attachments")
    seen_paths: set[str] = set()

    for raw_ref in raw_refs:
        ref = _strip_trailing_punct(raw_ref)
        abs_path = _resolve_at_path(ref, cwd)
        if not abs_path or abs_path in seen_paths:
            continue
        seen_paths.add(abs_path)
        if _is_excluded_path(abs_path):
            continue

        rel = _safe_relative_storage_path(abs_path, cwd)
        parts = [p for p in rel.split("/") if p]
        dest = os.path.join(base, *parts)
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        try:
            with open(abs_path, "rb") as f:
                raw = f.read()
        except OSError:
            continue

        if len(raw) > max_b:
            raw = raw[: max_b - 200] + b"\n... [truncated by TESTSIGMA_CONTEXT_FILE_MAX_BYTES]\n"

        try:
            with open(dest, "wb") as f:
                f.write(raw)
        except OSError:
            continue

        stored_rel = "/".join(["attachments"] + parts)
        idx: dict[str, Any] = {
            "tool_use_id": None,
            "tool_name": None,
            "kind": "prompt_reference",
            "source_file_path": abs_path,
            "stored_relative": stored_rel,
            "prompt_ref": ref,
        }
        _append_index(session_dir, idx)
        count += 1

    return count


def persist_tool_file_snapshots(session_id: str, event_data: dict[str, Any]) -> None:
    """
    On PostToolUse, persist snapshots under ``context_files/`` for Read / Write / Edit.
    """
    if _snapshots_disabled():
        return
    if event_data.get("hook_event_name") != "PostToolUse":
        return

    tool_name = (event_data.get("tool_name") or "").strip()
    tn = tool_name.lower()
    if tn not in ("read", "write", "edit"):
        return

    tool_input = event_data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return

    file_path = tool_input.get("file_path")
    if not file_path or not isinstance(file_path, str):
        return
    if _is_excluded_path(file_path):
        return

    cwd = str(event_data.get("cwd") or "")
    rel = _safe_relative_storage_path(file_path, cwd)
    session_dir = session_dir_for(session_id)
    base = os.path.join(session_dir, "context_files")
    parts = [p for p in rel.split("/") if p]
    if tn == "edit":
        parts[-1] = parts[-1] + ".edit.json"
    dest = os.path.join(base, *parts)
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    max_b = _max_bytes()
    content: str | None = None
    kind = tn

    if tn == "write":
        c = tool_input.get("content")
        if isinstance(c, str):
            content = c
    elif tn == "read":
        content = _extract_read_text(event_data.get("tool_response"))
    elif tn == "edit":
        # Store edit parameters as a reproducible patch record (no full file)
        old_s = tool_input.get("old_string")
        new_s = tool_input.get("new_string")
        patch_obj = {
            "file_path": file_path,
            "old_string": old_s if isinstance(old_s, str) else None,
            "new_string": new_s if isinstance(new_s, str) else None,
            "replace_all": tool_input.get("replace_all"),
        }
        content = json.dumps(patch_obj, ensure_ascii=False, indent=2)
        kind = "edit_patch"

    if content is None:
        return

    if len(content.encode("utf-8", errors="replace")) > max_b:
        content = content[: max_b - 200] + "\n... [truncated by TESTSIGMA_CONTEXT_FILE_MAX_BYTES]\n"

    try:
        with open(dest, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)
    except OSError:
        return

    tool_use_id = event_data.get("tool_use_id")
    stored_rel = "/".join(["context_files"] + parts)
    idx: dict[str, Any] = {
        "tool_use_id": tool_use_id,
        "tool_name": tool_name,
        "kind": kind,
        "source_file_path": file_path,
        "stored_relative": stored_rel,
    }
    _append_index(session_dir, idx)


def ensure_session_dirs(session_id: str) -> str:
    """Create session root and standard subdirs; return session directory path."""
    sdir = session_dir_for(session_id)
    for sub in ("attachments", "context_files"):
        os.makedirs(os.path.join(sdir, sub), exist_ok=True)
    return sdir
