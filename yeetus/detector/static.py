"""Static HTML / CSS / JS site detector."""

from __future__ import annotations

from pathlib import Path

from yeetus.detector.base import BaseDetector
from yeetus.models import Stack, StackInfo

# A directory is considered static when it has an index.html at its root.
# Glob fallback: any .html file at the root level.
_PRIMARY_MARKER = "index.html"

# If any of these exist, a more specific detector (Python / Node) should have
# already matched.  We check explicitly so the static detector is safe even
# when run in isolation or out of order.
_DISQUALIFIERS = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "uv.lock",
    "Pipfile",
]


class StaticDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "Static"

    def detect(self, path: Path) -> StackInfo | None:
        # Skip if another stack's markers are present.
        if any((path / marker).exists() for marker in _DISQUALIFIERS):
            return None

        # Require at least one HTML file at the root.
        if not (path / _PRIMARY_MARKER).exists():
            if not any(path.glob("*.html")):
                return None

        return StackInfo(stack=Stack.STATIC)
