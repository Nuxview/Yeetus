"""Node.js stack detector."""

from __future__ import annotations

import json
import re
from pathlib import Path

from open_di.detector.base import BaseDetector
from open_di.models import Stack, StackInfo

# Maps a canonical framework key to the npm package name to look for.
_FRAMEWORK_DEPS: dict[str, str] = {
    "next": "next",
    "vite": "vite",
    "react": "react",
    "vue": "vue",
    # Intentionally not included to reduce testing overhead:
    # They'll be WIP after the stable release
    # "nuxt": "nuxt",
    # "remix": "@remix-run/node",
    # "astro": "astro",
    # "express": "express",
    # "fastify": "fastify",
    # "koa": "koa",
    # "nestjs": "@nestjs/core",
    # "svelte": "svelte",
}

# Framework detection priority (first match wins).
_PRIORITY = [
    "next",
    "vite",
    "react",
    "vue",
    # Intentionally not included to reduce testing overhead:
    # They'll be WIP after the stable release
    # "nuxt",
    # "remix",
    # "astro",
    # "express",
    # "fastify",
    # "koa",
    # "vite",
    # "react",
    # "vue",
    # "svelte",
]

# Maps lockfile names to package manager identifiers.
_LOCKFILE_MAP: dict[str, str] = {
    "package-lock.json": "npm",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "bun.lockb": "bun",
}


class NodeDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "Node"

    def detect(self, path: Path) -> StackInfo | None:
        pkg_file = path / "package.json"
        if not pkg_file.exists():
            return None

        try:
            pkg: dict = json.loads(pkg_file.read_text())
        except (json.JSONDecodeError, OSError):
            # package.json exists but is unreadable — still a Node project.
            return StackInfo(stack=Stack.NODE)

        is_typescript = self._has_typescript(pkg)

        return StackInfo(
            stack=Stack.NODE,
            version=self._detect_version(path, pkg),
            framework=self._detect_framework(pkg),
            package_manager=self._detect_package_manager(path, pkg),
            extras={"is_typescript": is_typescript},
        )

    # ── helpers ────────────────────────────────────────────────────────────

    def _detect_version(self, path: Path, pkg: dict) -> str | None:
        # .nvmrc
        for fname in (".nvmrc", ".node-version"):
            nv = path / fname
            if nv.exists():
                raw = nv.read_text().strip().lstrip("v")
                m = re.match(r"(\d+)", raw)
                if m:
                    return m.group(1)

        # package.json engines.node
        engines = pkg.get("engines", {})
        m = re.search(r"(\d+)", engines.get("node", ""))
        if m:
            return m.group(1)

        return None

    def _detect_framework(self, pkg: dict) -> str | None:
        all_deps: dict[str, str] = {
            **pkg.get("dependencies", {}),
            **pkg.get("devDependencies", {}),
        }

        for key in _PRIORITY:
            dep_name = _FRAMEWORK_DEPS[key]
            if dep_name in all_deps:
                return key

        return None

    def _detect_package_manager(self, path: Path, pkg: dict) -> str:
        for lockfile, manager in _LOCKFILE_MAP.items():
            if (path / lockfile).exists():
                return manager

        # Explicit packageManager field (corepack)
        pm_field: str = pkg.get("packageManager", "")
        if pm_field.startswith("yarn"):
            return "yarn"
        if pm_field.startswith("pnpm"):
            return "pnpm"
        if pm_field.startswith("bun"):
            return "bun"

        return "npm"

    def _has_typescript(self, pkg: dict) -> bool:
        all_deps: dict[str, str] = {
            **pkg.get("dependencies", {}),
            **pkg.get("devDependencies", {}),
        }
        return "typescript" in all_deps
