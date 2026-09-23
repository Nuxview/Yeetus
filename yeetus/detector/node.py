import json
from pathlib import Path
from typing import Optional

from yeetus.detector.base import BaseDetector
from yeetus.models import StackInfo

class NodeDetector(BaseDetector):
    def detect(self, path: Path) -> Optional[StackInfo]:
        pkg_json = path / "package.json"
        if not pkg_json.exists():
            return None

        deps = {}
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))
        except Exception:
            pass

        # Framework detection hierarchy:
        # Check Next.js
        if "next" in deps:
            return StackInfo(
                stack_type="node",
                framework="nextjs",
                port=3000,
                cmd='["npm", "start"]',
                env_example="NODE_ENV=production\nPORT=3000\n",
                description="Node.js (Next.js)",
            )

        # Check Vite
        if "vite" in deps:
            return StackInfo(
                stack_type="node",
                framework="vite",
                port=5173,
                cmd='["npm", "run", "dev", "--", "--host"]',
                env_example="NODE_ENV=production\nPORT=5173\n",
                description="Node.js (Vite)",
            )

        # Check Vue
        if "vue" in deps:
            return StackInfo(
                stack_type="node",
                framework="vue",
                port=8080,
                cmd='["npm", "run", "serve"]',
                env_example="NODE_ENV=production\nPORT=8080\n",
                description="Node.js (Vue)",
            )

        # Check React
        if "react" in deps:
            return StackInfo(
                stack_type="node",
                framework="react",
                port=3000,
                cmd='["npm", "start"]',
                env_example="NODE_ENV=production\nPORT=3000\n",
                description="Node.js (React)",
            )

        # Default fallback for Node
        return StackInfo(
            stack_type="node",
            framework="node",
            port=3000,
            cmd='["npm", "start"]',
            env_example="NODE_ENV=production\nPORT=3000\n",
            description="Node.js Generic",
        )
