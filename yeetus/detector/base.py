from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from yeetus.models import StackInfo

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, path: Path) -> Optional[StackInfo]:
        """Detect tech stack from the given directory path."""
        pass
