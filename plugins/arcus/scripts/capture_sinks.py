"""
Pluggable sinks for Claude Code hook capture events.

Extend by implementing ``ContextCaptureSink`` (or a class with the same
``handle_event`` method) and wiring it in ``build_default_sinks``.

Default pipeline:

- ``ManifestSink`` — writes ``session_manifest.json`` only (grouping + TestSigma link state
  across hooks; each hook runs in a new process).
- ``EventsJSONLSink`` — appends every hook event as a JSON line to ``{session_dir}/events.jsonl``
  (local append-only audit trail, always active).
- ``WebhookSink`` — POSTs each event to ``{chitragupt_host}/api/v1/plugin/events`` when the
  AuthState (populated by ``/arcus:login``) carries a host.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from auth.state import AuthState
from auth.login import decode_jwt_claims


def _log(msg: str) -> None:
    line = f"[arcus:sinks] {msg}"
    if os.environ.get("ARCUS_DEBUG", "").strip() not in ("", "0", "false", "False"):
        print(line, file=sys.stderr, flush=True)
    try:
        log_path = os.path.join(plugin_data_dir(), "hook.log")
        with open(log_path, "a", encoding="utf-8") as _lf:
            import datetime
            _lf.write(f"{datetime.datetime.now().isoformat()} {line}\n")
    except Exception:
        pass

try:
    import fcntl  # type: ignore[attr-defined]
except ImportError:
    # Windows: no fcntl. Concurrent hook processes can race on manifest writes
    # and token refresh. Acceptable for single-user dev, but flag the limitation
    # so anyone running parallel hooks on Windows knows what to expect.
    fcntl = None
    if os.environ.get("ARCUS_DEBUG", "").strip() not in ("", "0", "false", "False"):
        print(
            "[arcus] warning: fcntl unavailable (Windows?). Concurrent hooks may race "
            "on manifest / token writes.",
            file=sys.stderr,
            flush=True,
        )

from session_grouping import merge_grouping_into_manifest
from ingest_attachments import build_ingest_attachments
from testsigma_session_link import (
    merge_testsigma_link,
    parse_workflow_ids_from_ingest_response,
)


class ContextCaptureSink(Protocol):
    """Handle a single normalized capture record."""

    def handle_event(self, record: dict[str, Any]) -> None:
        """Persist or forward ``record`` (must not raise into Claude Code)."""
        ...


def plugin_data_dir() -> str:
    claude_home = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    parts = plugin_root.rstrip("/").split("/")
    if len(parts) >= 4 and "cache" in parts:
        i = parts.index("cache")
        if i + 2 < len(parts):
            marketplace, plugin = parts[i + 1], parts[i + 2]
            return os.path.join(claude_home, "plugins", "data", f"{plugin}-{marketplace}")
    return os.path.join(claude_home, "plugins", "data", "arcus-inline")


def session_dir_for(session_id: str) -> str:
    root = os.environ.get("TESTSIGMA_CONTEXT_DIR") or plugin_data_dir()
    return os.path.join(root, "sessions", session_id)


def read_session_manifest(session_id: str) -> dict[str, Any] | None:
    """Load ``session_manifest.json`` for a session (after ``ManifestSink`` has run)."""
    try:
        path = os.path.join(session_dir_for(session_id), "session_manifest.json")
        if not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        return raw if isinstance(raw, dict) else None
    except Exception:
        return None


def _webhook_timeout_sec() -> float:
    try:
        return float(os.environ.get("TESTSIGMA_WORKFLOW_RESOLVE_TIMEOUT", "30"))
    except ValueError:
        return 30.0


def _webhook_max_retries() -> int:
    try:
        return max(1, int(os.environ.get("TESTSIGMA_CONTEXT_WEBHOOK_RETRIES", "3")))
    except ValueError:
        return 3


def _log_webhook_failure(record: dict[str, Any], err: str, session_id: str) -> None:
    """One JSON line to stderr for log aggregation (disable with ``TESTSIGMA_CONTEXT_WEBHOOK_LOG_FAILURES=false``)."""
    raw = (os.environ.get("TESTSIGMA_CONTEXT_WEBHOOK_LOG_FAILURES") or "true").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return
    if os.environ.get("ARCUS_DEBUG", "").strip() in ("", "0", "false", "False"):
        return
    try:
        line = json.dumps(
            {
                "event": "testsigma_webhook_failed",
                "session_id": session_id,
                "hook_event_name": record.get("hook_event_name"),
                "error": err,
            },
            ensure_ascii=False,
        )
        print(line, file=sys.stderr, flush=True)
    except Exception:
        pass


# --- Webhook circuit-breaker ------------------------------------------------
# Persist consecutive-failure count + a next-retry timestamp across hook
# processes so we don't hammer a dead endpoint on every tool call.

_CIRCUIT_THRESHOLD = 5         # open after this many consecutive failures
_CIRCUIT_MIN_BACKOFF = 300     # 5 min cooldown after threshold
_CIRCUIT_MAX_BACKOFF = 1800    # cap at 30 min


def _circuit_path() -> str:
    return os.path.join(plugin_data_dir(), "webhook_circuit.json")


def _circuit_open() -> bool:
    """True if the breaker is tripped and we're still inside the cooldown window."""
    try:
        with open(_circuit_path()) as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    nra = state.get("next_retry_at")
    if not nra:
        return False
    try:
        from datetime import datetime
        nra_dt = datetime.fromisoformat(nra.replace("Z", "+00:00"))
        from datetime import timezone as _tz
        return nra_dt > datetime.now(_tz.utc)
    except (ValueError, AttributeError):
        return False


def _circuit_record(success: bool) -> None:
    """Update breaker state after a POST attempt."""
    path = _circuit_path()
    try:
        with open(path) as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError):
        state = {}
    from datetime import datetime, timedelta, timezone as _tz
    if success:
        new_state = {"consecutive_failures": 0}
    else:
        n = int(state.get("consecutive_failures", 0)) + 1
        new_state: dict[str, Any] = {"consecutive_failures": n}
        if n >= _CIRCUIT_THRESHOLD:
            backoff = min(_CIRCUIT_MIN_BACKOFF * (2 ** (n - _CIRCUIT_THRESHOLD)), _CIRCUIT_MAX_BACKOFF)
            new_state["next_retry_at"] = (datetime.now(_tz.utc) + timedelta(seconds=backoff)).isoformat()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(new_state, f)
    except OSError as exc:
        _log(f"circuit-breaker write failed: {exc}")


def _post_ingest_with_retries(
    url: str,
    data: bytes,
    headers: dict[str, str],
    timeout: float,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    POST to ingest; retry transient failures (5xx, 429, network).

    Returns ``(parsed_json, None)`` on success, or ``(None, error_code)``.
    """
    retries = _webhook_max_retries()
    last_err: str | None = None
    for attempt in range(retries):
        req_headers = {**headers, "X-Request-ID": str(uuid.uuid4())}
        req = Request(url, data=data, headers=req_headers, method="POST")
        try:
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return None, "invalid_json_response"
            if not isinstance(parsed, dict):
                return None, "invalid_json_shape"
            return parsed, None
        except HTTPError as e:
            last_err = f"http_{e.code}"
            if attempt < retries - 1 and e.code in (429, 500, 502, 503, 504):
                time.sleep(min(0.5 * (2**attempt), 4.0))
                continue
            return None, last_err
        except (URLError, TimeoutError, OSError) as e:
            last_err = type(e).__name__
            if attempt < retries - 1:
                time.sleep(min(0.5 * (2**attempt), 4.0))
                continue
            return None, last_err
    return None, last_err or "unknown"


def apply_testsigma_from_events_response(
    session_dir: str,
    record: dict[str, Any],
    parsed: dict[str, Any] | None,
) -> None:
    """After ``POST /api/v1/plugin/events``, merge ``workflow_id`` / ``context_id`` into manifest."""
    hook_name = str(record.get("hook_event_name") or "").strip()
    if not hook_name:
        return
    manifest_path = os.path.join(session_dir, "session_manifest.json")
    if not os.path.isfile(manifest_path):
        return
    wf, ctx = parse_workflow_ids_from_ingest_response(parsed) if parsed else (None, None)
    if wf:
        try:
            from auth.config import read_config, write_config
            cfg = read_config()
            if cfg and cfg.get("active_workflow_id") != wf:
                cfg["active_workflow_id"] = wf
                write_config(cfg)
        except Exception as exc:
            _log(f"apply_testsigma: active_workflow_id update failed: {exc}")
    try:
        with open(manifest_path, "a+", encoding="utf-8") as mf:
            if fcntl:
                fcntl.flock(mf.fileno(), fcntl.LOCK_EX)
            try:
                mf.seek(0)
                raw = mf.read()
                manifest = json.loads(raw) if raw.strip() else {}
                if not isinstance(manifest, dict):
                    manifest = {}
                ts = manifest.setdefault("testsigma", {})

                if hook_name == "UserPromptSubmit":
                    if ts.get("ticket_resolve_done"):
                        return
                    gk = manifest.get("grouping_keys") or {}
                    tu = gk.get("ticket_ids_union") if isinstance(gk, dict) else None
                    if isinstance(tu, list) and tu:
                        if wf:
                            ts["workflow_id"] = wf
                            ts["context_id"] = ctx or wf
                            ts["link_source"] = "api"
                            ts["session_group_key"] = wf
                            ts["ticket_resolve_done"] = True
                        else:
                            ts["link_source"] = "api_failed"
                    return

                if hook_name == "SessionStart" or not ts.get("workflow_id"):
                    if wf:
                        ts["workflow_id"] = wf
                        ts["context_id"] = ctx or wf
                        ts["link_source"] = "api"
                        ts["session_group_key"] = wf
                    elif ts.get("link_source") == "pending":
                        ts["link_source"] = "api_failed"
                mf.seek(0)
                mf.truncate()
                json.dump(manifest, mf, indent=2, ensure_ascii=False)
            finally:
                if fcntl:
                    fcntl.flock(mf.fileno(), fcntl.LOCK_UN)
    except Exception as exc:
        _log(f"apply_testsigma: manifest update failed: {exc}")


class ManifestSink:
    """
    Persist ``session_manifest.json`` under the session directory (grouping keys,
    TestSigma 1:N link). Hook events themselves are sent by ``WebhookSink``, not
    written to ``events.jsonl``.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        self._base = base_dir  # if None, use env / default per session_dir_for

    def handle_event(self, record: dict[str, Any]) -> None:
        try:
            payload = record.get("payload") or {}
            session_id = str(payload.get("session_id") or payload.get("conversation_id") or "unknown-session")
            hook_name = str(record.get("hook_event_name") or "Unknown")
            _log(f"hook={hook_name} session={session_id} payload={json.dumps(payload)}")
            sdir = (
                os.path.join(self._base, "sessions", session_id)
                if self._base
                else session_dir_for(session_id)
            )
            os.makedirs(sdir, exist_ok=True)

            manifest_path = os.path.join(sdir, "session_manifest.json")
            with open(manifest_path, "a+", encoding="utf-8") as mf:
                if fcntl:
                    fcntl.flock(mf.fileno(), fcntl.LOCK_EX)
                try:
                    mf.seek(0)
                    body = mf.read()
                    if body.strip():
                        try:
                            manifest = json.loads(body)
                        except json.JSONDecodeError:
                            manifest = {}
                    else:
                        manifest = {}
                    manifest.setdefault("session_id", session_id)
                    if payload.get("cwd"):
                        manifest["cwd"] = payload["cwd"]
                    if payload.get("transcript_path"):
                        manifest["transcript_path"] = payload["transcript_path"]
                    manifest["last_hook"] = hook_name
                    manifest["updated_at"] = record.get("received_at", "")
                    merge_grouping_into_manifest(manifest, payload, hook_name)
                    merge_testsigma_link(manifest, session_id, hook_name, payload)
                    mf.seek(0)
                    mf.truncate()
                    json.dump(manifest, mf, indent=2, ensure_ascii=False)
                finally:
                    if fcntl:
                        fcntl.flock(mf.fileno(), fcntl.LOCK_UN)
        except Exception as exc:
            _log(f"ManifestSink: write failed: {exc}")


class WebhookSink:
    """
    POST JSON record to a remote endpoint. Disabled when no host is configured.

    After ``ManifestSink``, attaches ``metadata.session_manifest`` (current
    ``session_manifest.json``) so ingest can resolve ``workflow_id`` and return it in the
    response; this sink applies those ids back into ``session_manifest.json``.

    Host + account_id are read from the SSO config (``/arcus:login``).
    Env knobs (all optional):
      ``TESTSIGMA_WORKFLOW_RESOLVE_TIMEOUT`` (seconds, default 30);
      ``TESTSIGMA_CONTEXT_WEBHOOK_RETRIES`` (default 3);
      ``TESTSIGMA_CONTEXT_WEBHOOK_LOG_FAILURES`` (default ``true``);
      ``TESTSIGMA_CONTEXT_INCLUDE_FILES`` (default ``true``);
      ``TESTSIGMA_INGEST_MAX_ATTACHMENT_BYTES`` (default 20 MiB per file);
      ``TESTSIGMA_SENSITIVE_PATTERNS`` (comma-separated globs to extend the denylist).
    """

    def __init__(
        self,
        url: str | None = None,
        account_id: str | None = None,
        timeout_sec: float | None = None,
    ) -> None:
        self._auth = AuthState.load()
        self._timeout = timeout_sec if timeout_sec is not None else _webhook_timeout_sec()

        # Soft-disable when not authenticated. Hook still runs; webhook silent.
        if not self._auth.usable():
            _log("WebhookSink: not authenticated, run /arcus:login")
            self._url = None
            self._account_id = None
            return

        host = (self._auth.api_server or "").rstrip("/")
        if not host:
            _log("WebhookSink: no testsigma host configured")
            self._url = None
            self._account_id = None
            return

        self._url = url.strip() if url else (host + "/api/v1/plugin/events")
        # Preload an access token so we can extract account_id eagerly for
        # request-shape compatibility with prior env-based account tagging.
        token = self._auth.access_token()
        if account_id:
            self._account_id = account_id.strip() or None
        elif token:
            self._account_id = str(decode_jwt_claims(token).get("account_id", "")) or None
        else:
            self._account_id = None
        _log(f"WebhookSink init: url={self._url!r} authed=True timeout={self._timeout}s")

    def handle_event(self, record: dict[str, Any]) -> None:
        if self._url is None or not self._auth.usable():
            _log("WebhookSink: skipping event (not authenticated)")
            return

        if _circuit_open():
            _log("WebhookSink: circuit-breaker open, skipping POST (endpoint marked unhealthy)")
            return

        token = self._auth.access_token()
        if token is None:
            _log("WebhookSink: skipping event (token unavailable; run /arcus:login)")
            return

        payload = record.get("payload") or {}
        session_id = str(payload.get("session_id") or payload.get("conversation_id") or "unknown-session")
        hook_name = record.get("hook_event_name", "?")
        _log(f"WebhookSink: POST {self._url} hook={hook_name} session={session_id}")
        sdir = session_dir_for(session_id)
        manifest = read_session_manifest(session_id)
        outbound: dict[str, Any] = dict(record)
        meta: dict[str, Any] = outbound["metadata"] if isinstance(outbound.get("metadata"), dict) else {}

        if manifest is not None:
            meta["session_manifest"] = manifest

        if self._auth.config:
            project_id = (self._auth.config.get("project_id") or "").strip()
            if project_id:
                outbound["project_id"] = project_id

        gk = manifest.get("grouping_keys") if isinstance(manifest, dict) else {}
        if not isinstance(gk, dict):
            gk = {}

        # account_id: stored on self first, then event payload fallback.
        account_id = self._account_id or str(payload.get("account_id") or "").strip() or None

        for key, value in (
            ("account_id", account_id),
            ("git_repo", gk.get("git_repo")),
            ("git_branch", gk.get("git_branch")),
            ("git_user_email", gk.get("git_user_email")),
        ):
            if value:
                meta[key] = value

        ingest_att = build_ingest_attachments(sdir, outbound)
        if ingest_att:
            meta["ingest_attachments"] = ingest_att

        if meta:
            outbound["metadata"] = meta
        data = json.dumps(outbound).encode("utf-8")
        _log(f"WebhookSink: payload size={len(data)} bytes, attachments={len(ingest_att) if ingest_att else 0}")
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "x-agentic-token": token,
        }
        url = self._url
        parsed, err = _post_ingest_with_retries(url, data, headers, self._timeout)
        if err:
            _log(f"WebhookSink: POST failed — {err}")
            _log_webhook_failure(record, err, session_id)
            if err == "http_401":
                self._auth.mark_unauthed()
                _log("WebhookSink: session revoked (401 from server)")
                # 401 is an auth problem, not an endpoint health problem — don't trip breaker.
            else:
                _circuit_record(success=False)
        else:
            _log(f"WebhookSink: POST success — response keys={list(parsed.keys()) if parsed else 'none'}")
            _circuit_record(success=True)
        apply_testsigma_from_events_response(sdir, record, parsed)


class EventsJSONLSink:
    """
    Append every hook event as a single JSON line to ``{session_dir}/events.jsonl``.

    This gives a local, append-only audit trail of all hook events for the session,
    independent of the remote webhook (which may be unconfigured).
    """

    def handle_event(self, record: dict[str, Any]) -> None:
        try:
            payload = record.get("payload") or {}
            session_id = str(payload.get("session_id") or payload.get("conversation_id") or "unknown-session")
            sdir = session_dir_for(session_id)
            os.makedirs(sdir, exist_ok=True)
            events_path = os.path.join(sdir, "events.jsonl")
            line = json.dumps(record, ensure_ascii=False) + "\n"
            with open(events_path, "a", encoding="utf-8") as f:
                if fcntl:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(line)
                finally:
                    if fcntl:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as exc:
            _log(f"EventsJSONLSink: write failed: {exc}")


class CompositeSink:
    """Run multiple sinks in order."""

    def __init__(self, sinks: list[ContextCaptureSink]) -> None:
        self._sinks = sinks

    def handle_event(self, record: dict[str, Any]) -> None:
        for sink in self._sinks:
            try:
                sink.handle_event(record)
            except Exception as exc:  # noqa: BLE001
                _log(f"{type(sink).__name__}: handle_event raised — {exc}")


def build_default_sinks() -> ContextCaptureSink:
    """
    Default: update local ``session_manifest.json``, append to ``events.jsonl``, then POST
    each record to the ingest API when the AuthState (from ``/arcus:login``) carries a
    host. ``WebhookSink`` no-ops when unauthenticated.

    Replace this factory to plug in your own sinks, e.g.::

        CompositeSink([ManifestSink(), EventsJSONLSink(), S3Sink(), WebhookSink(url=...)])
    """
    sinks: list = [ManifestSink(), EventsJSONLSink()]
    try:
        sinks.append(WebhookSink())
    except Exception as exc:  # noqa: BLE001
        _log(f"build_default_sinks: WebhookSink disabled — {exc}")
    return CompositeSink(sinks)
