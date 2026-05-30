"""
Build ``metadata.ingest_attachments`` for POST /api/v1/context/events so the ingest server can
persist blobs that only exist on the client (externalized base64, context_files snapshots).

Env:
  TESTSIGMA_INGEST_MAX_ATTACHMENT_BYTES — max bytes per file inlined (default 20 MiB).
  TESTSIGMA_CONTEXT_INCLUDE_FILES — set to ``false`` to skip (default ``true``).
  TESTSIGMA_SENSITIVE_PATTERNS — comma-separated globs to extend the built-in
    sensitive-file denylist (e.g. ``environment.json,*.secret``).
"""

from __future__ import annotations

import base64
import fnmatch
import hashlib
import json
import os
from typing import Any


_SENSITIVE_BASENAMES = frozenset({
    ".env",
    ".envrc",
    ".netrc",
    ".pgpass",
    "credentials",
    "credentials.json",
    "credentials.yaml",
    "credentials.yml",
    "secrets.json",
    "secrets.yaml",
    "secrets.yml",
    "gcp_key.json",
    "gcp-key.json",
    "htpasswd",
    ".htpasswd",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
})
_SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".keystore", ".jks")


def _custom_sensitive_patterns() -> list[str]:
    """Comma-separated globs from ``TESTSIGMA_SENSITIVE_PATTERNS`` (case-insensitive)."""
    raw = os.environ.get("TESTSIGMA_SENSITIVE_PATTERNS", "").strip()
    if not raw:
        return []
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def _is_sensitive_path(path: str) -> bool:
    """Return True if *path* looks like a secrets/credentials file that must never be sent."""
    if not path:
        return False

    basename_lower = os.path.basename(path).lower()
    norm = path.replace("\\", "/").lower()

    if basename_lower in _SENSITIVE_BASENAMES:
        return True
    if fnmatch.fnmatch(basename_lower, ".env.*"):
        return True
    if fnmatch.fnmatch(basename_lower, "service-account*.json"):
        return True
    if basename_lower.endswith(_SENSITIVE_SUFFIXES):
        return True

    components = norm.split("/")
    if ".ssh" in components or ".gnupg" in components:
        return True
    if norm.endswith(".aws/credentials"):
        return True
    if norm.endswith(".gcloud/legacy_credentials"):
        return True

    for pat in _custom_sensitive_patterns():
        if fnmatch.fnmatch(basename_lower, pat) or fnmatch.fnmatch(norm, pat):
            return True

    return False


def _max_attachment_bytes() -> int:
    try:
        return int(os.environ.get("TESTSIGMA_INGEST_MAX_ATTACHMENT_BYTES", str(20 * 1024 * 1024)))
    except ValueError:
        return 20 * 1024 * 1024


def _include_files() -> bool:
    return os.environ.get("TESTSIGMA_CONTEXT_INCLUDE_FILES", "true").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _walk_externalized_paths(obj: Any, out: list[str]) -> None:
    if isinstance(obj, dict):
        if obj.get("_externalized") is True and isinstance(obj.get("path"), str):
            p = obj["path"].strip()
            if p and p not in out:
                out.append(p)
        for v in obj.values():
            _walk_externalized_paths(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk_externalized_paths(v, out)


def _last_index_entry(index_path: str) -> dict[str, Any] | None:
    """Return the last JSON line (``persist_tool_file_snapshots`` appends one line per PostToolUse)."""
    entries = _last_n_index_entries(index_path, 1)
    return entries[0] if entries else None


def _last_n_index_entries(index_path: str, n: int) -> list[dict[str, Any]]:
    """Return the last *n* JSON-line entries from a JSONL index file."""
    try:
        with open(index_path, encoding="utf-8", errors="replace") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]
    except OSError:
        return []
    result: list[dict[str, Any]] = []
    for line in lines[-n:]:
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                result.append(row)
        except json.JSONDecodeError:
            pass
    return result


def build_ingest_attachments(session_dir: str, record: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Collect files to send alongside the webhook JSON.

    Returns a list of dicts with ``content_base64``, ``relative_key``, ``kind``, etc.
    ``session_dir`` is the absolute path to ``sessions/<session_id>/``.
    """
    if not _include_files():
        return []

    max_b = _max_attachment_bytes()
    sdir = session_dir
    out: list[dict[str, Any]] = []
    seen_sha256: set[str] = set()

    def add_file(
        kind: str,
        abs_path: str,
        relative_key: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if not abs_path or not os.path.isfile(abs_path):
            return
        # Sensitive-path guard: check abs_path, relative_key, and source hints
        # so symlinked / re-keyed snapshots can't slip through.
        candidates = [abs_path, relative_key]
        if extra:
            for k in ("client_path", "source_file_path"):
                v = extra.get(k)
                if isinstance(v, str):
                    candidates.append(v)
        if any(_is_sensitive_path(c) for c in candidates):
            out.append({
                "kind": kind,
                "relative_key": relative_key.replace("\\", "/"),
                "skipped": True,
                "reason": "sensitive_path",
            })
            return
        try:
            raw = open(abs_path, "rb").read()
        except OSError:
            return
        h = hashlib.sha256(raw).hexdigest()
        if h in seen_sha256:
            return
        if len(raw) > max_b:
            row: dict[str, Any] = {
                "kind": kind,
                "relative_key": relative_key,
                "skipped": True,
                "reason": "too_large",
                "byte_length": len(raw),
                "max_bytes": max_b,
            }
            if extra:
                row.update(extra)
            out.append(row)
            return
        seen_sha256.add(h)
        row = {
            "kind": kind,
            "relative_key": relative_key.replace("\\", "/"),
            "sha256": h,
            "byte_length": len(raw),
            "content_base64": base64.b64encode(raw).decode("ascii"),
        }
        if extra:
            row.update(extra)
        out.append(row)

    payload = record.get("payload")
    if isinstance(payload, dict):
        paths: list[str] = []
        _walk_externalized_paths(payload, paths)
        for p in paths:
            add_file("externalized_blob", p, f"attachments/{os.path.basename(p)}", {"client_path": p})

        hook = str(record.get("hook_event_name") or "")
        if hook == "PostToolUse":
            tn = (payload.get("tool_name") or "").strip().lower()
            if tn in ("read", "write", "edit"):
                idx_path = os.path.join(sdir, "context_files_index.jsonl")
                entry = _last_index_entry(idx_path)
                if isinstance(entry, dict):
                    sr = entry.get("stored_relative")
                    if isinstance(sr, str) and sr:
                        fp = os.path.join(sdir, *sr.split("/"))
                        add_file(
                            "context_snapshot",
                            fp,
                            sr.replace("\\", "/"),
                            {
                                "tool_name": entry.get("tool_name"),
                                "source_file_path": entry.get("source_file_path"),
                            },
                        )

        if hook == "UserPromptSubmit":
            prompt_ref_count = payload.get("_prompt_ref_count")
            if isinstance(prompt_ref_count, int) and prompt_ref_count > 0:
                idx_path = os.path.join(sdir, "context_files_index.jsonl")
                entries = _last_n_index_entries(idx_path, prompt_ref_count)
                for entry in entries:
                    if entry.get("kind") != "prompt_reference":
                        continue
                    sr = entry.get("stored_relative")
                    if isinstance(sr, str) and sr:
                        fp = os.path.join(sdir, *sr.split("/"))
                        add_file(
                            "prompt_reference",
                            fp,
                            sr.replace("\\", "/"),
                            {
                                "source": "prompt_reference",
                                "source_file_path": entry.get("source_file_path"),
                                "prompt_ref": entry.get("prompt_ref"),
                            },
                        )

    return out
