"""127.0.0.1 loopback HTTP listener for plugin auth flow.

Single-use: accepts the first POST to /auth-token whose body's `state` matches
the expected state, then shuts down. If no valid POST arrives within
`timeout_seconds`, `wait_for_result` returns None.
"""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


class LoopbackListener:
    def __init__(self, expected_state: str, timeout_seconds: float = 300.0):
        self._state = expected_state
        self._timeout = timeout_seconds
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._result: dict[str, Any] | None = None
        self._got_result = threading.Event()

    def start(self) -> None:
        listener = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                return

            def _cors(self):
                origin = self.headers.get("Origin", "*")
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Access-Control-Max-Age", "600")

            def do_OPTIONS(self):  # noqa: N802
                self.send_response(204)
                self._cors()
                self.end_headers()

            def do_POST(self):  # noqa: N802
                if self.path != "/auth-token":
                    self.send_response(404)
                    self._cors()
                    self.end_headers()
                    return
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b""
                try:
                    body = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self.send_response(400)
                    self._cors()
                    self.end_headers()
                    self.wfile.write(b"invalid json")
                    return
                if body.get("state") != listener._state:
                    self.send_response(400)
                    self._cors()
                    self.end_headers()
                    self.wfile.write(b"state mismatch")
                    return
                listener._result = body
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
                listener._got_result.set()
                # Single-use: shut down after the first valid POST
                shutdown_thread = threading.Thread(
                    target=listener.stop, daemon=True
                )
                shutdown_thread.start()

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def address(self) -> tuple[str, int]:
        assert self._server is not None
        host, port = self._server.server_address[:2]
        return str(host), int(port)

    def wait_for_result(self, timeout: float | None = None) -> dict[str, Any] | None:
        wait = self._timeout if timeout is None else timeout
        if not self._got_result.wait(wait):
            return None
        return self._result

    def stop(self) -> None:
        if self._server is not None:
            try:
                self._server.shutdown()
                self._server.server_close()
            except Exception:
                pass
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
