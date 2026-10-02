import contextlib
import re
from pathlib import Path

from yeetus.detector.base import BaseDetector
from yeetus.models import StackInfo


class PythonDetector(BaseDetector):
    def detect(self, path: Path) -> StackInfo | None:
        markers = [
            path / m
            for m in (
                "requirements.txt",
                "pyproject.toml",
                "uv.lock",
                "Pipfile",
                "setup.py",
            )
        ]

        if not any(m.exists() for m in markers) and (
            (path / "package.json").exists() or not any(path.glob("*.py"))
        ):
            return None

        combined_text = ""
        for m in markers:
            if m.exists() and m.is_file():
                with contextlib.suppress(OSError, UnicodeDecodeError):
                    combined_text += m.read_text(encoding="utf-8") + "\n"

        # Check framework in combined_text
        if re.search(r"(?i)\bfastapi\b", combined_text):
            return StackInfo(
                stack_type="python",
                framework="fastapi",
                port=8000,
                cmd='["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]',
                env_example="PORT=8000\nHOST=0.0.0.0\n",
                description="Python (FastAPI)",
                entrypoint="main.py",
            )
        elif re.search(r"(?i)\bflask\b", combined_text):
            return StackInfo(
                stack_type="python",
                framework="flask",
                port=5000,
                cmd='["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]',
                env_example="FLASK_APP=app.py\nFLASK_ENV=production\nPORT=5000\n",
                description="Python (Flask)",
                entrypoint="app.py",
            )
        elif (
            re.search(r"(?i)\bdjango\b", combined_text) or (path / "manage.py").exists()
        ):
            return StackInfo(
                stack_type="python",
                framework="django",
                port=8000,
                cmd='["python", "manage.py", "runserver", "0.0.0.0:8000"]',
                env_example="SECRET_KEY=change-me-in-production\nDEBUG=False\nALLOWED_HOSTS=localhost,127.0.0.1\nPORT=8000\n",
                description="Python (Django)",
                entrypoint="manage.py",
            )

        # Default fallback for Python
        return StackInfo(
            stack_type="python",
            framework="python",
            port=5000,
            cmd='["python", "app.py"]',
            env_example="PORT=5000\n",
            description="Python Generic",
            entrypoint="app.py",
        )
