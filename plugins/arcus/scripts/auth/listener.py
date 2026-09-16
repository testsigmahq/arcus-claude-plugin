"""127.0.0.1 loopback HTTP listener for plugin auth flow.

Single-use: accepts the first POST to /auth-token whose body's `state` matches
the expected state, then shuts down. If no valid POST arrives within
`timeout_seconds`, `wait_for_result` returns None.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import hostos


class _AuthHTTPServer(HTTPServer):
    # On Windows SO_REUSEADDR lets another local process bind this port and take
    # the auth code. POSIX has no such hijack, and reuse avoids TIME_WAIT there.
    allow_reuse_address = not hostos.WINDOWS


class LoopbackListener:
    def __init__(self, expected_state: str, timeout_seconds: float = 300.0):
        self._state = expected_state
        self._timeout = timeout_seconds
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._result: dict[str, Any] | None = None
        self._got_result = threading.Event()
        self._stopping = threading.Event()

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

            def do_OPTIONS(self):
                self.send_response(204)
                self._cors()
                self.end_headers()

            def do_POST(self):
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
                self.wfile.flush()
                self.close_connection = True
                listener._got_result.set()  # _serve exits once this handler returns

        self._server = _AuthHTTPServer(("127.0.0.1", 0), Handler)
        self._server.timeout = 0.5  # so _serve notices a stop between requests
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        """Serve one request at a time until a result arrives or we are stopped.

        Not ``serve_forever``: the socket must close only after a handler has
        returned, or the browser's POST can be reset mid-response.
        """
        try:
            while not self._stopping.is_set() and not self._got_result.is_set():
                self._server.handle_request()
        finally:
            try:
                self._server.server_close()
            except OSError:
                pass

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
        self._stopping.set()
        if self._thread is not None and self._thread.is_alive() and threading.current_thread() is not self._thread:
            self._thread.join(timeout=3.0)
        if self._server is not None:
            try:
                self._server.server_close()
            except OSError:
                pass
