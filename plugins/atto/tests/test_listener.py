import json
import socket
import threading
import time
import urllib.request

import pytest

from auth.listener import LoopbackListener


def _post(url: str, body: dict) -> int:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def test_listener_binds_to_loopback_only():
    listener = LoopbackListener(expected_state="abc", timeout_seconds=2)
    listener.start()
    try:
        host, port = listener.address()
        assert host == "127.0.0.1"
        # Verify the server socket is bound exclusively to 127.0.0.1, not 0.0.0.0
        import sys
        if sys.platform != "darwin":
            # On Linux, connecting to 0.0.0.0:port when only 127.0.0.1 is bound fails
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            try:
                with pytest.raises((ConnectionRefusedError, socket.timeout, OSError)):
                    s.connect(("0.0.0.0", port))
            finally:
                s.close()
        else:
            # On macOS, 0.0.0.0 routes to loopback; verify bind address directly
            assert listener._server is not None
            assert listener._server.server_address[0] == "127.0.0.1"
    finally:
        listener.stop()


def test_accepts_valid_post_then_shuts():
    listener = LoopbackListener(expected_state="state-xyz", timeout_seconds=5)
    listener.start()
    host, port = listener.address()
    status = _post(
        f"http://{host}:{port}/auth-token",
        {"code": "test-code", "state": "state-xyz"},
    )
    assert status == 200
    received = listener.wait_for_result(timeout=2)
    assert received == {"code": "test-code", "state": "state-xyz"}
    with pytest.raises(Exception):
        _post(f"http://{host}:{port}/auth-token", {"code": "x", "state": "state-xyz"})


def test_rejects_state_mismatch():
    listener = LoopbackListener(expected_state="correct", timeout_seconds=5)
    listener.start()
    host, port = listener.address()
    try:
        status = _post(
            f"http://{host}:{port}/auth-token",
            {"code": "y", "state": "wrong"},
        )
        assert status == 400
        status2 = _post(
            f"http://{host}:{port}/auth-token",
            {"code": "y", "state": "correct"},
        )
        assert status2 == 200
    finally:
        listener.stop()


def test_timeout_returns_none():
    listener = LoopbackListener(expected_state="abc", timeout_seconds=0.5)
    listener.start()
    received = listener.wait_for_result(timeout=2)
    assert received is None
    listener.stop()
