import re

import pytest

from support import PLUGIN_ROOT, markdown_files

POINTER = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+\.md)")


@pytest.mark.parametrize("doc", markdown_files(), ids=lambda p: str(p.relative_to(PLUGIN_ROOT.parents[1])))
def test_every_pointer_resolves(doc):
    for target in POINTER.findall(doc.read_text(encoding="utf-8")):
        assert (PLUGIN_ROOT / target).exists(), f"{doc.name} points at {target}, which does not exist"
