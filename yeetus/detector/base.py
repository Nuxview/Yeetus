from abc import ABC, abstractmethod
from pathlib import Path

from yeetus.models import StackInfo


class BaseDetector(ABC):
    @abstractmethod
    def detect(self, path: Path) -> StackInfo | None:
        """Detect tech stack from the given directory path."""
