"""Core data models for open-di."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Stack(str, Enum):
    PYTHON = "python"
    NODE = "node"


class BoilerplateLevel(str, Enum):
    MINIMAL = "minimal"
    FULL = "full"


@dataclass
class StackInfo:
    """Describes the detected (or manually specified) tech stack for one service."""

    stack: Stack
    version: Optional[str] = None
    """Runtime version string, e.g. '3.12' for Python or '20' for Node."""
    framework: Optional[str] = None
    """Identified framework, e.g. 'fastapi', 'next', 'express'."""
    package_manager: Optional[str] = None
    """Package manager in use: 'pip'/'uv'/'poetry' for Python; 'npm'/'yarn'/'pnpm' for Node."""
    extras: dict = field(default_factory=dict)
    """Catch-all for stack-specific metadata (e.g. {'is_typescript': True})."""

    def display(self) -> str:
        """Return a short human-readable description, e.g. 'python v3.12 (fastapi) [uv]'."""
        parts = [self.stack.value]
        if self.version:
            parts.append(f"v{self.version}")
        if self.framework:
            parts.append(f"({self.framework})")
        if self.package_manager:
            parts.append(f"[{self.package_manager}]")
        return " ".join(parts)


@dataclass
class ProjectPart:
    """One logical service/part of the project (e.g. a backend, a frontend)."""

    name: str
    """Service name used in compose.yaml, e.g. 'backend'."""
    path: str
    """Path relative to the project root, e.g. './backend'."""
    stack_info: StackInfo
    boilerplate: BoilerplateLevel
    port: Optional[int] = None
    """Host port to expose, e.g. 8000."""
    env_vars: dict[str, str] = field(default_factory=dict)


@dataclass
class ComposeService:
    """Representation of one service within compose.yaml."""

    name: str
    build_context: str
    port: Optional[int] = None
    depends_on: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    volumes: list[str] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)


@dataclass
class ComposeConfig:
    """In-memory representation of the full compose.yaml to be rendered."""

    services: list[ComposeService] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
