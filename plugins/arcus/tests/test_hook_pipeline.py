import json
import os
import sys
import subprocess
from pathlib import Path

import pytest


def test_hook_runs_to_completion_without_auth(tmp_path, monkeypatch):
    """End-to-end: run capture_hook.py with no auth; pipe a fake event in.
    Expect: exit 0, no traceback in stderr.
    """
    env = {**os.environ}
    env["CLAUDE_CONFIG_DIR"] = str(tmp_path)
    env.pop("CLAUDE_PLUGIN_ROOT", None)

    repo = Path(__file__).parents[1]
    script = repo / "scripts" / "capture_hook.py"
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "session_id": "s-test",
        "tool_input": {},
    })
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=payload, capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    assert "Traceback" not in proc.stderr, f"unexpected traceback: {proc.stderr}"
