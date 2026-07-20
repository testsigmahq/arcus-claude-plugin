from unittest.mock import MagicMock

import pytest

from capture_sinks import WebhookSink, build_default_sinks, CompositeSink


def test_webhook_sink_init_no_raise_when_unconfigured(monkeypatch):
    """Original bug fix: ctor must not raise when no auth config exists."""
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    sink = WebhookSink()  # MUST NOT RAISE
    record = {"hook_event_name": "PreToolUse", "payload": {"session_id": "s"}}
    sink.handle_event(record)  # silent no-op


def test_build_default_sinks_includes_webhook_when_ctor_succeeds():
    sink = build_default_sinks()
    assert isinstance(sink, CompositeSink)
    types_present = [type(s).__name__ for s in sink._sinks]
    assert "ManifestSink" in types_present
    assert "EventsJSONLSink" in types_present
    assert "WebhookSink" in types_present


def test_composite_sink_isolates_failures():
    failing = MagicMock()
    failing.handle_event.side_effect = RuntimeError("boom")
    failing.__class__.__name__ = "BoomSink"
    after = MagicMock()
    after.__class__.__name__ = "AfterSink"

    composite = CompositeSink([failing, after])
    composite.handle_event({"hook_event_name": "X", "payload": {}})
    after.handle_event.assert_called_once()
