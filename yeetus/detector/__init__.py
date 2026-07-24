"""Stack detection — runs all detectors and returns the first match."""

from __future__ import annotations

from pathlib import Path

# Imported lazily inside detect_stack to avoid circular-import issues at
# package initialisation time, but the imports are fine here in practice.
from yeetus.detector.node import NodeDetector
from yeetus.detector.python import PythonDetector
from yeetus.detector.static import StaticDetector
from yeetus.models import StackInfo

# Order matters: more specific detectors run first so that, e.g., a Node
# project with an index.html is not misidentified as a static site.
_DETECTORS = [
    PythonDetector(),
    NodeDetector(),
    StaticDetector(),
]


def detect_stack(path: Path) -> StackInfo | None:
    """Run every registered detector against *path* and return the first match.

    Returns ``None`` when no detector recognises the stack.
    """
    for detector in _DETECTORS:
        result = detector.detect(path)
        if result is not None:
            return result
    return None


__all__ = ["detect_stack"]
