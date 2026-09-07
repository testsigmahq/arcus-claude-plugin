"""What a user actually receives when the plugin installs.

Claude Code installs the whole plugin directory. Verified against the installed
cache rather than the documentation, which does not say: other plugins there
carry `node_modules`, `.git`, `package-lock.json`, changelogs and screenshots.
There is no `files` field and no ignore mechanism, so anything left in this
directory reaches every user of it.

Separate from `test_document_shape.py` deliberately: these change for
packaging reasons, and that module's tests change for authoring reasons.
"""

from support import PLUGIN_ROOT

# --- what the install actually contains --------------------------------------

#: Claude Code installs the whole plugin directory. Verified against the
#: installed cache, which carries `node_modules`, `.git`, `package-lock.json`,
#: changelogs and screenshots for other plugins — there is no `files` field and
#: no ignore mechanism, so anything left here reaches every user.
_WORKING_NOTE = ("handoff", "research-")


def test_no_working_note_ships_inside_the_plugin():
    stray = [
        path.name
        for path in sorted(PLUGIN_ROOT.glob("*.md"))
        if path.name.lower().startswith(_WORKING_NOTE)
    ]
    assert not stray, (
        f"these install into every user's plugin cache: {stray}. Development "
        f"notes belong outside the plugin directory."
    )


def test_the_plugin_has_a_readme():
    # The file a person opens first, and the one file every installed official
    # plugin carries.
    readme = PLUGIN_ROOT / "README.md"
    assert readme.exists(), "the plugin root has no README.md"
    flat = " ".join(readme.read_text(encoding="utf-8").split()).lower()
    assert "survey" in flat, "it must name the entry point"
    assert "resume" in flat, "and the command that picks a Migration back up"
    assert "testsigma" in flat and "cli" in flat, "and the dependency it needs"
    assert "context.md" in flat, "and where the vocabulary is defined"
