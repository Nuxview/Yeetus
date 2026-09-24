from pathlib import Path

from yeetus.detector.base import BaseDetector
from yeetus.models import StackInfo


class StaticDetector(BaseDetector):
    def detect(self, path: Path) -> StackInfo | None:
        index_html = path / "index.html"
        pkg_json = path / "package.json"
        
        if index_html.exists() and not pkg_json.exists():
            return StackInfo(
                stack_type="static",
                framework="static",
                port=80,
                cmd='["nginx", "-g", "daemon off;"]',
                env_example="PORT=80\n",
                description="Static HTML (Nginx)",
            )
        return None
