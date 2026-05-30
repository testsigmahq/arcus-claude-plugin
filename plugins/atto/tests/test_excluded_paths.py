"""Default noise-exclusion list for context snapshots."""
from __future__ import annotations

import pytest

from session_context_storage import _is_excluded_path


@pytest.mark.parametrize(
    "path",
    [
        "/repo/node_modules/react/index.js",
        "/repo/frontend/.next/server/page.js",
        "/repo/dist/bundle.js",
        "/repo/build/output.o",
        "/repo/.git/HEAD",
        "/repo/__pycache__/mod.cpython-312.pyc",
        "/repo/.venv/lib/python3.12/site-packages/foo.py",
        "/repo/target/debug/app",
        "/repo/vendor/github.com/x/y.go",
        "/repo/ios/Pods/Foo/Foo.m",
        "/repo/pkg.egg-info/PKG-INFO",
        "C:\\repo\\node_modules\\x\\y.js",
    ],
)
def test_excluded(path: str) -> None:
    assert _is_excluded_path(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "/repo/src/index.js",
        "/repo/app/main.py",
        "/repo/README.md",
        "/repo/lib/util.ts",
        "",
    ],
)
def test_not_excluded(path: str) -> None:
    assert _is_excluded_path(path) is False


def test_custom_patterns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESTSIGMA_EXCLUDE_PATTERNS", "*.generated.ts,fixtures")
    assert _is_excluded_path("/repo/src/api.generated.ts") is True
    assert _is_excluded_path("/repo/test/fixtures/data.json") is True
    assert _is_excluded_path("/repo/src/api.ts") is False
