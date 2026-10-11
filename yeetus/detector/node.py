import contextlib
import json
import re
from pathlib import Path

from yeetus.detector.base import BaseDetector
from yeetus.models import StackInfo

PM_LOCKFILES = {
    "bun": ("bun.lockb", "bun.lock", "bunfig.toml"),
    "pnpm": ("pnpm-lock.yaml", "pnpm-workspace.yaml", ".pnpmfile.cjs"),
    "yarn": ("yarn.lock", ".yarnrc.yml", ".yarnrc"),
    "npm": ("package-lock.json", "npm-shrinkwrap.json", ".npmrc"),
}

FRAMEWORKS = (
    ("next", "nextjs", 3000, '["npm", "start"]', "Node.js (Next.js)"),
    ("vite", "vite", 5173, '["npm", "run", "dev", "--", "--host"]', "Node.js (Vite)"),
    ("vue", "vue", 8080, '["npm", "run", "serve"]', "Node.js (Vue)"),
    ("react", "react", 3000, '["npm", "start"]', "Node.js (React)"),
)


class NodeDetector(BaseDetector):
    def detect_package_manager(self, path: Path, data: dict | None = None) -> str:
        if data and isinstance(pm := data.get("packageManager"), str):
            for candidate in ("pnpm", "yarn", "bun", "npm"):
                if pm.startswith(candidate):
                    return candidate

        for pm_name, files in PM_LOCKFILES.items():
            if any((path / f).exists() for f in files):
                return pm_name

        return "npm"

    def detect(self, path: Path) -> StackInfo | None:
        pkg_json = path / "package.json"
        if not pkg_json.exists():
            return None

        data, deps = {}, {}
        with contextlib.suppress(json.JSONDecodeError, OSError):
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))

        package_manager = self.detect_package_manager(path, data)
        package_manager_version = ""
        declaration = data.get("packageManager", "")
        if isinstance(declaration, str) and declaration.startswith(
            f"{package_manager}@"
        ):
            version = declaration.split("@", 1)[1].split("+", 1)[0]
            if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", version):
                package_manager_version = version

        for dep, framework, port, cmd, desc in FRAMEWORKS:
            if dep in deps:
                break
        else:
            framework, port, cmd, desc = (
                "node",
                3000,
                '["npm", "start"]',
                "Node.js Generic",
            )

        return StackInfo(
            stack_type="node",
            framework=framework,
            port=port,
            cmd=cmd,
            env_example=f"NODE_ENV=production\nPORT={port}\n",
            description=desc,
            package_manager_version=package_manager_version,
        ).with_package_manager(package_manager)
