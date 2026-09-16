import json
import os
import socket
import urllib.error
import urllib.request

import pytest
from auth.listener import LoopbackListener


def _post(url: str, body: dict) -> int:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def test_listener_binds_to_loopback_only():
    """The auth listener must never be reachable from off-box.

    Asserts the bound address directly rather than probing 0.0.0.0: connecting
    there routes to loopback on Linux and macOS alike, so the probe succeeded
    and proved nothing.
    """
    listener = LoopbackListener(expected_state="abc", timeout_seconds=2)
    listener.start()
    try:
        host, port = listener.address()
        assert host == "127.0.0.1"
        assert listener._server is not None
        assert listener._server.server_address[0] == "127.0.0.1"

        # A non-loopback local address must not answer.
        outward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        outward.settimeout(0.5)
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except OSError:
            local_ip = None
        try:
            if local_ip and not local_ip.startswith("127."):
                with pytest.raises((ConnectionRefusedError, socket.timeout, TimeoutError, OSError)):
                    outward.connect((local_ip, port))
        finally:
            outward.close()
    finally:
        listener.stop()


def test_listener_does_not_reuse_addresses_on_windows():
    """SO_REUSEADDR lets another local process bind the same port on Windows."""
    from auth import listener as listener_mod

    assert listener_mod._AuthHTTPServer.allow_reuse_address == (os.name != "nt")


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
    # Single-use: the server is down, so the second POST cannot connect at all.
    # (_post swallows HTTPError, so only a transport failure escapes.)
    with pytest.raises(urllib.error.URLError):
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
