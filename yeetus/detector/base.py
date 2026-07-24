"""Abstract base class that every stack detector must implement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from yeetus.models import StackInfo


class BaseDetector(ABC):
    """Shared interface for all stack detectors.

    A concrete detector inspects a directory on disk and returns a
    :class:`~open_di.models.StackInfo` when it recognises the stack,
    or ``None`` when the stack is not applicable.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable detector name (e.g. ``'Python'``)."""
        ...

    @abstractmethod
    def detect(self, path: Path) -> StackInfo | None:
        """Inspect *path* and return :class:`~open_di.models.StackInfo` or ``None``.

        Args:
            path: Absolute path to the service directory.

        Returns:
            A :class:`~open_di.models.StackInfo` when the stack is detected,
            ``None`` otherwise.
        """
        ...
