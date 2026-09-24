import contextlib
import json
from pathlib import Path

from yeetus.detector.base import BaseDetector
from yeetus.models import StackInfo


class NodeDetector(BaseDetector):
    def detect_package_manager(self, path: Path, data: dict | None = None) -> str:
        if data:
            pm_field = data.get("packageManager", "")
            if isinstance(pm_field, str):
                if pm_field.startswith("pnpm"):
                    return "pnpm"
                if pm_field.startswith("yarn"):
                    return "yarn"
                if pm_field.startswith("bun"):
                    return "bun"
                if pm_field.startswith("npm"):
                    return "npm"

        # Check configuration & lock files for bun
        bun_files = ["bun.lockb", "bun.lock", "bunfig.toml"]
        if any((path / f).exists() for f in bun_files):
            return "bun"

        # Check configuration & lock files for pnpm
        pnpm_files = ["pnpm-lock.yaml", "pnpm-workspace.yaml", ".pnpmfile.cjs"]
        if any((path / f).exists() for f in pnpm_files):
            return "pnpm"

        # Check configuration & lock files for yarn
        yarn_files = ["yarn.lock", ".yarnrc.yml", ".yarnrc"]
        if any((path / f).exists() for f in yarn_files):
            return "yarn"

        # Check configuration & lock files for npm
        npm_files = ["package-lock.json", "npm-shrinkwrap.json", ".npmrc"]
        if any((path / f).exists() for f in npm_files):
            return "npm"

        return "npm"

    def detect(self, path: Path) -> StackInfo | None:
        pkg_json = path / "package.json"
        if not pkg_json.exists():
            return None

        data = {}
        deps = {}
        with contextlib.suppress(json.JSONDecodeError, OSError):
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))

        package_manager = self.detect_package_manager(path, data)

        # Framework detection hierarchy:
        # Check Next.js
        if "next" in deps:
            info = StackInfo(
                stack_type="node",
                framework="nextjs",
                port=3000,
                cmd='["npm", "start"]',
                env_example="NODE_ENV=production\nPORT=3000\n",
                description="Node.js (Next.js)",
            )
        # Check Vite
        elif "vite" in deps:
            info = StackInfo(
                stack_type="node",
                framework="vite",
                port=5173,
                cmd='["npm", "run", "dev", "--", "--host"]',
                env_example="NODE_ENV=production\nPORT=5173\n",
                description="Node.js (Vite)",
            )
        # Check Vue
        elif "vue" in deps:
            info = StackInfo(
                stack_type="node",
                framework="vue",
                port=8080,
                cmd='["npm", "run", "serve"]',
                env_example="NODE_ENV=production\nPORT=8080\n",
                description="Node.js (Vue)",
            )
        # Check React
        elif "react" in deps:
            info = StackInfo(
                stack_type="node",
                framework="react",
                port=3000,
                cmd='["npm", "start"]',
                env_example="NODE_ENV=production\nPORT=3000\n",
                description="Node.js (React)",
            )
        # Default fallback for Node
        else:
            info = StackInfo(
                stack_type="node",
                framework="node",
                port=3000,
                cmd='["npm", "start"]',
                env_example="NODE_ENV=production\nPORT=3000\n",
                description="Node.js Generic",
            )

        return info.with_package_manager(package_manager)
