"""
Tests for session_grouping.py — specifically ticket_ids_union aggregation.
"""
import session_grouping
from session_grouping import merge_grouping_into_manifest


def test_ticket_ids_union_includes_branch_tickets(monkeypatch):
    monkeypatch.setattr(session_grouping, "_run_cmd", lambda *a, **kw: None)
    manifest = {}
    payload = {"git_branch": "feature/PROJ-123-add-login", "cwd": "/tmp"}
    merge_grouping_into_manifest(manifest, payload, hook_name="SessionStart")
    gk = manifest["grouping_keys"]
    assert "PROJ-123" in (gk.get("ticket_ids_union") or [])


def test_ticket_ids_union_dedups_across_sources(monkeypatch):
    monkeypatch.setattr(session_grouping, "_run_cmd", lambda *a, **kw: None)
    manifest = {}
    payload = {"git_branch": "feature/PROJ-123-x", "cwd": "/tmp"}
    merge_grouping_into_manifest(manifest, payload, hook_name="SessionStart")
    payload2 = {"prompt": "fixing PROJ-123 and PROJ-456", "cwd": "/tmp"}
    merge_grouping_into_manifest(manifest, payload2, hook_name="UserPromptSubmit")
    gk = manifest["grouping_keys"]
    assert sorted(gk["ticket_ids_union"]) == ["PROJ-123", "PROJ-456"]


def test_grouping_keys_only_contains_server_consumed_fields(monkeypatch):
    monkeypatch.setattr(session_grouping, "_run_cmd", lambda *a, **kw: None)
    manifest = {}
    payload = {"git_branch": "feature/PROJ-1-x", "cwd": "/tmp"}
    merge_grouping_into_manifest(manifest, payload, hook_name="SessionStart")
    payload2 = {"prompt": "fix PROJ-2", "cwd": "/tmp"}
    merge_grouping_into_manifest(manifest, payload2, hook_name="UserPromptSubmit")
    gk = manifest["grouping_keys"]
    for removed in (
        "ticket_ids_from_branch",
        "ticket_ids_from_prompts",
        "ticket_ids_from_first_prompt",
        "signal_sources",
        "recommended_signals",
        "first_user_prompt_preview",
    ):
        assert removed not in gk, f"{removed} should be removed from grouping_keys"
    assert sorted(gk["ticket_ids_union"]) == ["PROJ-1", "PROJ-2"]
    allowed = {"git_repo", "git_user_email", "git_user_name", "ticket_ids_union",
               "git_branches_union", "git_branch"}
    assert set(gk.keys()) <= allowed, f"Unexpected fields: {set(gk.keys()) - allowed}"


def test_git_name_captured(monkeypatch):
    def fake_run_cmd(cmd, cwd):
        if cmd[:3] == ["git", "config", "user.name"]:
            return "Aayush Raj"
        return None
    monkeypatch.setattr(session_grouping, "_run_cmd", fake_run_cmd)
    manifest = {}
    merge_grouping_into_manifest(manifest, {"cwd": "/tmp"}, hook_name="SessionStart")
    assert manifest["grouping_keys"].get("git_user_name") == "Aayush Raj"
