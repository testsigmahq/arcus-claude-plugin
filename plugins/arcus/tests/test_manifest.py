import re

from support import MANIFEST, MARKETPLACE, PLUGIN_ROOT, load_json


def test_manifest_names_the_plugin():
    manifest = load_json(MANIFEST)
    assert manifest["name"] == "arcus"
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
    assert manifest["privacyPolicy"]


def test_marketplace_lists_it_with_the_same_description():
    manifest = load_json(MANIFEST)
    entry = next(p for p in load_json(MARKETPLACE)["plugins"] if p["name"] == "arcus")
    assert entry["source"] == "./plugins/arcus"
    assert entry["description"] == manifest["description"]


def test_nothing_captures_or_sends_by_itself():
    """The plugin has no hooks and no scripts: the CLI is the only thing that talks to Arcus."""
    assert "hooks" not in load_json(MANIFEST)
    for name in ("hooks", "scripts"):
        assert not (PLUGIN_ROOT / name).exists(), f"{name}/ must not exist"
    code = [p for p in PLUGIN_ROOT.rglob("*.py") if "tests" not in p.relative_to(PLUGIN_ROOT).parts]
    assert code == []
