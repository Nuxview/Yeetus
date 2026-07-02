"""Python stack detector."""

from __future__ import annotations

import re
from pathlib import Path

from open_di.detector.base import BaseDetector
from open_di.models import Stack, StackInfo

# Any of these files signals a Python project.
_MARKERS = [
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "uv.lock",
]

# Maps package names (lowercase) to a canonical framework identifier.
_FRAMEWORK_MAP: dict[str, str] = {
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    "uvicorn": "uvicorn",
    # Intentionally not included to reduce testing overhead:
    # They'll be WIP after the stable release
    # "starlette": "starlette",
    # "litestar": "litestar",
    # "sanic": "sanic",
    # "tornado": "tornado",
}


class PythonDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "Python"

    def detect(self, path: Path) -> StackInfo | None:
        if not any((path / marker).exists() for marker in _MARKERS):
            return None

        return StackInfo(
            stack=Stack.PYTHON,
            version=self._detect_version(path),
            framework=self._detect_framework(path),
            package_manager=self._detect_package_manager(path),
        )

    # ── helpers ────────────────────────────────────────────────────────────

    def _detect_version(self, path: Path) -> str | None:
        # pyenv / mise style .python-version
        pv = path / ".python-version"
        if pv.exists():
            m = re.match(r"(\d+\.\d+)", pv.read_text().strip())
            if m:
                return m.group(1)

        # pyproject.toml requires-python = ">=3.11"
        pyproject = path / "pyproject.toml"
        if pyproject.exists():
            m = re.search(
                r'requires-python\s*=\s*"[>=~^<! ]*(\d+\.\d+)',
                pyproject.read_text(),
            )
            if m:
                return m.group(1)

        return None

    def _detect_framework(self, path: Path) -> str | None:
        candidates: list[str] = []

        req = path / "requirements.txt"
        if req.exists():
            candidates.append(req.read_text().lower())

        pyproject = path / "pyproject.toml"
        if pyproject.exists():
            candidates.append(pyproject.read_text().lower())

        for content in candidates:
            for pkg, framework in _FRAMEWORK_MAP.items():
                # Match package name at start of a line (requirements) or
                # as a dependency string inside toml.
                if re.search(rf"(?:^|\n|\"|'){re.escape(pkg)}[>=\[<\n\"',]", content):
                    return framework

        return None

    def _detect_package_manager(self, path: Path) -> str:
        if (path / "uv.lock").exists():
            return "uv"
        if (path / "poetry.lock").exists():
            return "poetry"
        if (path / "Pipfile").exists():
            return "pipenv"
        return "pip"
