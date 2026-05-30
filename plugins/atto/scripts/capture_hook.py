#!/usr/bin/env python3
"""
Claude Code hook handler: read JSON from stdin, normalize, dispatch via
:class:`capture_sinks.ContextCaptureSink` (local manifest + ingest API for events).

Environment (all optional — auth/host now come from /atto:login config.json):
  CLAUDE_CONFIG_DIR    — Claude home (default: ~/.claude); data goes under {claude_home}/plugins/data/atto
  TESTSIGMA_CONTEXT_DIR — override output root
  TESTSIGMA_EXTERNALIZE_MIN_BYTES — min string size to externalize as file (default 65536)
  TESTSIGMA_DISABLE_CONTEXT_FILE_SNAPSHOTS — set to ``true`` to skip context_files/ snapshots
  TESTSIGMA_CONTEXT_FILE_MAX_BYTES — max bytes per context_files snapshot (default 50 MiB)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def _log(msg: str) -> None:
    if os.environ.get("ATTO_DEBUG", "").strip() not in ("", "0", "false", "False"):
        print(f"[atto] {msg}", file=sys.stderr, flush=True)


from capture_sinks import build_default_sinks, session_dir_for
from session_context_storage import ensure_session_dirs, persist_prompt_file_references, persist_tool_file_snapshots
from auth.state import AuthState

_AUTH_WARN_HOOKS = {"SessionStart", "UserPromptSubmit"}


def _auth_warning_state() -> str | None:
    """Return 'revoked', 'missing', or None when auth is usable."""
    try:
        auth = AuthState.load()
    except Exception:
        return None
    if auth.usable():
        return None
    if auth.config and auth.config.get("auth_status") == "revoked":
        return "revoked"
    return "missing"


def _emit_auth_warning_if_needed(session_id: str, hook_name: str) -> None:
    """Print a one-shot systemMessage JSON to stdout when unauthed. Throttled per session+state."""
    if hook_name not in _AUTH_WARN_HOOKS:
        return
    state = _auth_warning_state()
    if state is None:
        return
    marker = os.path.join(session_dir_for(session_id), ".auth_warning_state")
    try:
        with open(marker, encoding="utf-8") as f:
            if f.read().strip() == state:
                return
    except OSError:
        pass
    if state == "revoked":
        msg = "⚠️ atto: session expired. Please run /atto:login to resume Testsigma capture."
    else:
        msg = "⚠️ atto: not logged in. Run /atto:login to enable Testsigma capture."
    try:
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        with open(marker, "w", encoding="utf-8") as f:
            f.write(state)
    except OSError:
        pass
    print(json.dumps({"systemMessage": msg}), flush=True)

BASE64_HINT = re.compile(r"^[A-Za-z0-9+/=\s]+$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _externalize_threshold() -> int:
    try:
        return int(os.environ.get("TESTSIGMA_EXTERNALIZE_MIN_BYTES", "65536"))
    except ValueError:
        return 65536


def _should_externalize_string(s: str, threshold: int) -> bool:
    if len(s) < threshold:
        return False
    # Heuristic: very long single-line base64 or similar binary-as-text
    compact = "".join(s.split())
    if len(compact) < threshold:
        return False
    sample = compact[:8000]
    if not BASE64_HINT.match(sample):
        return False
    # Try decode a small prefix; base64 has length multiple of 4 (padded)
    try:
        pad = (-len(compact)) % 4
        trial = compact[: min(len(compact), 4096 + pad)]
        trial += "=" * ((-len(trial)) % 4)
        base64.b64decode(trial[:4096], validate=True)
        return True
    except Exception:
        return False


def _ext_from_magic(raw: bytes) -> str:
    if len(raw) >= 4 and raw[:4] == b"\x89PNG":
        return ".png"
    if len(raw) >= 2 and raw[:2] == b"\xff\xd8":
        return ".jpg"
    if len(raw) >= 4 and raw[:4] == b"%PDF":
        return ".pdf"
    if len(raw) >= 6 and raw[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return ".webp"
    return ".bin"


def _write_blob(session_id: str, raw: bytes, ext: str) -> tuple[str, str]:
    h = hashlib.sha256(raw).hexdigest()[:16]
    name = f"{h}_{uuid.uuid4().hex[:8]}{ext}"
    attach_dir = os.path.join(session_dir_for(session_id), "attachments")
    os.makedirs(attach_dir, exist_ok=True)
    path = os.path.join(attach_dir, name)
    with open(path, "wb") as f:
        f.write(raw)
    return path, h


def _externalize_base64_string(session_id: str, s: str) -> dict[str, Any] | None:
    """Decode base64 to bytes and write under attachments/. Returns ref dict or None."""
    compact = "".join(s.split())
    if not compact:
        return None
    try:
        raw = base64.b64decode(compact, validate=True)
    except Exception:
        return None
    if not raw:
        return None
    ext = _ext_from_magic(raw)
    path, short_hash = _write_blob(session_id, raw, ext)
    return {
        "_externalized": True,
        "sha256_prefix": short_hash,
        "byte_length": len(raw),
        "path": path,
    }


def _externalize_image_shaped_dict(session_id: str, d: dict[str, Any]) -> Any | None:
    """
    Claude Code often sends images as structured JSON (not one huge string), e.g.:
    {type: image, source: {type: base64, data: ...}}
    {type: image, file: {base64: ..., type: image/jpeg}}
    {toolUseResult: {type: image, file: {base64: ...}}}
    """
    t = d.get("type")
    if t == "image":
        src = d.get("source")
        if isinstance(src, dict) and src.get("type") == "base64":
            data = src.get("data")
            if isinstance(data, str):
                ref = _externalize_base64_string(session_id, data)
                if ref:
                    media = src.get("media_type")
                    if isinstance(media, str):
                        ref = {**ref, "media_type": media}
                    return ref
        file = d.get("file")
        if isinstance(file, dict) and isinstance(file.get("base64"), str):
            ref = _externalize_base64_string(session_id, file["base64"])
            if ref:
                mt = file.get("type")
                if isinstance(mt, str):
                    ref = {**ref, "media_type": mt}
                return ref
    tur = d.get("toolUseResult")
    if isinstance(tur, dict) and tur.get("type") == "image":
        file = tur.get("file")
        if isinstance(file, dict) and isinstance(file.get("base64"), str):
            ref = _externalize_base64_string(session_id, file["base64"])
            if ref:
                mt = file.get("type")
                if isinstance(mt, str):
                    ref = {**ref, "media_type": mt}
                return {**d, "toolUseResult": ref}
    return None


def _sanitize_value(session_id: str, obj: Any, threshold: int) -> Any:
    if isinstance(obj, dict):
        ext_img = _externalize_image_shaped_dict(session_id, obj)
        if ext_img is not None:
            return ext_img
        return {k: _sanitize_value(session_id, v, threshold) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_value(session_id, v, threshold) for v in obj]
    if isinstance(obj, str):
        if _should_externalize_string(obj, threshold):
            ref = _externalize_base64_string(session_id, obj)
            if ref is not None:
                return ref
        return obj
    return obj


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    try:
        event_data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = str(event_data.get("session_id") or event_data.get("conversation_id") or "unknown-session")
    hook_name = str(event_data.get("hook_event_name") or "").strip()
    if not hook_name:
        _log(f"skipping event with no hook_event_name (session={session_id})")
        sys.exit(0)
    threshold = _externalize_threshold()

    try:
        ensure_session_dirs(session_id)
        persist_tool_file_snapshots(session_id, event_data)
        prompt_ref_count = persist_prompt_file_references(session_id, event_data)
        if prompt_ref_count > 0:
            event_data["_prompt_ref_count"] = prompt_ref_count
    except Exception:
        pass

    try:
        sanitized = _sanitize_value(session_id, event_data, threshold)
    except Exception:
        sanitized = event_data

    record = {
        "received_at": _utc_now(),
        "hook_event_name": hook_name,
        "payload": sanitized,
    }

    _log(f"hook={hook_name} session={session_id}")

    try:
        sink = build_default_sinks()
        sink.handle_event(record)
    except Exception as exc:  # noqa: BLE001
        _log(f"sink pipeline error: {exc}")

    try:
        _emit_auth_warning_if_needed(session_id, hook_name)
    except Exception as exc:  # noqa: BLE001
        _log(f"auth warning emit failed: {exc}")

    sys.exit(0)


if __name__ == "__main__":
    main()
