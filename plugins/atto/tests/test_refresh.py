import json
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
import io

import pytest

from auth import refresh


def _fake_resp(status: int, body: dict) -> MagicMock:
    m = MagicMock()
    m.status = status
    m.read.return_value = json.dumps(body).encode()
    m.__enter__.return_value = m
    return m


def test_refresh_success_returns_pair():
    with patch("auth.refresh.urlopen") as urlopen:
        urlopen.return_value = _fake_resp(200, {
            "data": {
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 86400,
                "token_type": "Bearer",
            }
        })
        pair = refresh.refresh_tokens(
            host="https://chitragupt.example",
            uuid="abc",
            refresh_token="old-refresh",
        )
    assert pair is not None
    assert pair["access_token"] == "new-access"
    assert pair["refresh_token"] == "new-refresh"


def test_refresh_returns_none_on_401():
    err = HTTPError(
        url="x", code=401, msg="Unauthorized", hdrs=None,
        fp=io.BytesIO(b"refresh failed"),
    )
    with patch("auth.refresh.urlopen", side_effect=err):
        pair = refresh.refresh_tokens(
            host="https://chitragupt.example",
            uuid="abc",
            refresh_token="old-refresh",
        )
    assert pair is None


def test_refresh_returns_none_on_network_error():
    with patch("auth.refresh.urlopen", side_effect=OSError("conn refused")):
        pair = refresh.refresh_tokens(
            host="https://chitragupt.example",
            uuid="abc",
            refresh_token="old-refresh",
        )
    assert pair is None
