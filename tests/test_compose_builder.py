from pathlib import Path
import pytest

from yeetus.compose_builder import ComposeBuilder, PortCollisionError
from yeetus.models import ProjectPart, StackInfo

def make_dummy_part(name: str, path: Path, port: int, stack_type: str = "python", framework: str = "flask", level: str = "minimal", depends_on=None):
    stack_info = StackInfo(
        stack_type=stack_type,
        framework=framework,
        port=port,
        cmd='["python", "app.py"]',
    )
    return ProjectPart(
        name=name,
        path=path,
        stack_info=stack_info,
        port=port,
        level=level,
        depends_on=depends_on or [],
    )

def test_compose_builder_single_service(tmp_path):
    builder = ComposeBuilder(tmp_path)
    part = make_dummy_part("web", tmp_path, port=5000)
    config = builder.build([part])
    assert len(config.services) == 1
    assert config.services[0].name == "web"
    assert config.services[0].context == "."
    assert config.services[0].port == 5000

def test_compose_builder_multi_service(tmp_path):
    backend_dir = tmp_path / "backend"
    frontend_dir = tmp_path / "frontend"
    backend_dir.mkdir()
    frontend_dir.mkdir()

    builder = ComposeBuilder(tmp_path)
    api_part = make_dummy_part("api", backend_dir, port=8000, framework="fastapi")
    web_part = make_dummy_part("web", frontend_dir, port=3000, stack_type="node", framework="react", depends_on=["api"])

    config = builder.build([api_part, web_part])
    assert len(config.services) == 2
    assert config.services[0].name == "api"
    assert config.services[0].context == "backend"
    assert config.services[0].port == 8000
    
    assert config.services[1].name == "web"
    assert config.services[1].context == "frontend"
    assert config.services[1].port == 3000
    assert config.services[1].depends_on == ["api"]

def test_compose_builder_port_collision(tmp_path):
    p1 = tmp_path / "svc1"
    p2 = tmp_path / "svc2"
    p1.mkdir()
    p2.mkdir()

    builder = ComposeBuilder(tmp_path)
    s1 = make_dummy_part("svc1", p1, port=8080)
    s2 = make_dummy_part("svc2", p2, port=8080)

    with pytest.raises(PortCollisionError, match="Port collision detected"):
        builder.build([s1, s2])
