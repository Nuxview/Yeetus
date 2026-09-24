import shutil
import subprocess

from tests.conftest import FIXTURES_DIR
from yeetus.detector import detect_stack
from yeetus.generator import Generator
from yeetus.models import ProjectPart


def test_multi_project_generation(tmp_path):
    backend_dir = tmp_path / "backend"
    frontend_dir = tmp_path / "frontend"
    backend_dir.mkdir()
    frontend_dir.mkdir()

    # Copy FastAPI fixture into backend
    for item in (FIXTURES_DIR / "python-fastapi").iterdir():
        if item.is_file():
            shutil.copy2(item, backend_dir / item.name)

    # Copy React fixture into frontend
    for item in (FIXTURES_DIR / "node-react").iterdir():
        if item.is_file():
            shutil.copy2(item, frontend_dir / item.name)

    backend_stack = detect_stack(backend_dir)
    assert backend_stack is not None
    assert backend_stack.framework == "fastapi"

    frontend_stack = detect_stack(frontend_dir)
    assert frontend_stack is not None
    assert frontend_stack.framework == "react"

    backend_part = ProjectPart(
        name="api",
        path=backend_dir,
        stack_info=backend_stack,
        level="full",
    )
    frontend_part = ProjectPart(
        name="web",
        path=frontend_dir,
        stack_info=frontend_stack,
        level="minimal",
        depends_on=["api"],
    )

    generator = Generator()
    generated_files = generator.generate(tmp_path, [backend_part, frontend_part])

    # Check that Dockerfile was created in both subdirectories
    assert (backend_dir / "Dockerfile").exists()
    assert (backend_dir / ".env.example").exists()
    assert (frontend_dir / "Dockerfile").exists()
    assert not (frontend_dir / ".env.example").exists()

    # Check unified compose.yaml at root
    compose_path = tmp_path / "compose.yaml"
    assert compose_path.exists()
    compose_content = compose_path.read_text()
    assert "api:" in compose_content
    assert "context: backend" in compose_content
    assert "web:" in compose_content
    assert "context: frontend" in compose_content
    assert "- api" in compose_content

    # Run `docker compose config`
    proc = subprocess.run(["docker", "compose", "config"], cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 0, f"`docker compose config` failed:\n{proc.stderr}"
