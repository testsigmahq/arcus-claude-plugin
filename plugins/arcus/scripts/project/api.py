"""HTTP client for plugin-facing project endpoints on agentic-test."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from auth.state import AuthState


def list_projects(auth: AuthState, search: str | None = None, timeout: float = 15.0) -> list[dict[str, Any]] | None:
    """GET /api/v1/plugin/projects with bearer access_token. Returns list or None."""
    host = (auth.api_server or "").rstrip("/")
    token = auth.access_token()
    if not host or not token:
        return None
    qs = f"?{urlencode({'search': search})}" if search else ""
    url = f"{host}/api/v1/plugin/projects{qs}"
    req = Request(url, method="GET", headers={"x-agentic-token": token})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        print(f"arcus: list projects failed ({e.code}): {e.read().decode()[:200]}")
        return None
    except (URLError, OSError, json.JSONDecodeError) as e:
        print(f"arcus: list projects error: {e}")
        return None
    return data.get("projects") or []


def patch_workflow_project(auth: AuthState, workflow_id: str, project_id: str, timeout: float = 15.0) -> bool:
    """PATCH /api/v1/context/workflows/<wf>/project to update an existing workflow."""
    host = (auth.api_server or "").rstrip("/")
    token = auth.access_token()
    if not host or not token:
        return False
    url = f"{host}/api/v1/context/workflows/{workflow_id}/project"
    body = json.dumps({"project_id": project_id}).encode("utf-8")
    req = Request(
        url,
        data=body,
        method="PATCH",
        headers={"x-agentic-token": token, "Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except (HTTPError, URLError, OSError) as e:
        print(f"arcus: patch workflow project failed: {e}")
        return False
