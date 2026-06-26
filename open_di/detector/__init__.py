"""Stack detection — runs all detectors and returns the first match."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

# Imported lazily inside detect_stack to avoid circular-import issues at
# package initialisation time, but the imports are fine here in practice.
from open_di.detector.node import NodeDetector
from open_di.detector.python import PythonDetector
from open_di.models import StackInfo

_DETECTORS = [
    PythonDetector(),
    NodeDetector(),
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
