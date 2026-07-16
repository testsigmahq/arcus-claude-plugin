"""
TestSigma 1:N linking: many Claude sessions -> one workflow / context record.

Persisted under ``session_manifest.json`` -> ``testsigma``:

- ``workflow_id`` / ``context_id`` — TestSigma-side key (same value unless API returns both).
- ``claude_session_id`` — this hook session (the ``N`` side of 1:N).

Resolution: HTTP via ``WebhookSink`` -> ``POST {chitragupt_host}/api/v1/plugin/events``: ingest
resolves workflow from ``metadata.session_manifest`` and returns ``workflow_id`` / ``context_id``;
the plugin applies them to ``session_manifest.json`` after each hook. The first
``UserPromptSubmit`` with ``ticket_ids_union`` non-empty triggers a second apply so ingest can
merge ticket keys with an earlier branch-only workflow.
"""

from __future__ import annotations

import json
from typing import Any


def parse_workflow_ids_from_ingest_response(
    parsed: dict[str, Any] | None,
) -> tuple[str | None, str | None]:
    """
    Parse workflow/context ids from ``POST /api/v1/context/events`` JSON.

    Supports top-level or ``data`` wrapper.
    """
    if not isinstance(parsed, dict):
        return None, None
    inner = parsed
    if "data" in parsed and isinstance(parsed["data"], dict):
        inner = parsed["data"]
    wf = inner.get("workflow_id") or inner.get("workflowId")
    ctx = inner.get("context_id") or inner.get("contextId")
    if isinstance(wf, str):
        wf = wf.strip() or None
    else:
        wf = None
    if isinstance(ctx, str):
        ctx = ctx.strip() or None
    else:
        ctx = None
    if wf and not ctx:
        ctx = wf
    if ctx and not wf:
        wf = ctx
    return wf, ctx


def merge_testsigma_link(
    manifest: dict[str, Any],
    session_id: str,
    hook_name: str,
    payload: dict[str, Any],
) -> None:
    """Mutate ``manifest`` with a ``testsigma`` block for 1:N linking."""
    ts = manifest.setdefault("testsigma", {})
    ts["claude_session_id"] = session_id

    if hook_name == "SessionStart":
        if ts.get("workflow_id"):
            ts.setdefault("session_group_key", ts.get("workflow_id"))
            return
        ts["link_source"] = "pending"
        return

    if hook_name == "UserPromptSubmit":
        if ts.get("ticket_resolve_done"):
            return
        gk = manifest.get("grouping_keys") or {}
        if not isinstance(gk, dict):
            return
        tu = gk.get("ticket_ids_union")
        if not isinstance(tu, list) or not tu:
            return
        ts["link_source"] = "pending"
        return
