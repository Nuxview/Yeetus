from pathlib import Path
from typing import List, Optional

from yeetus.detector.base import BaseDetector
from yeetus.detector.node import NodeDetector
from yeetus.detector.python import PythonDetector
from yeetus.detector.static import StaticDetector
from yeetus.models import StackInfo

DETECTORS: list[BaseDetector] = [
    PythonDetector(),
    NodeDetector(),
    StaticDetector(),
]

def detect_stack(path: Path) -> StackInfo | None:
    for detector in DETECTORS:
        detected = detector.detect(path)
        if detected:
            return detected
    return None
