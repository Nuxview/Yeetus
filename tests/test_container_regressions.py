import json
import os
import shutil

import pytest

from tests.conftest import FIXTURES_DIR
from tests.docker_helpers import build_and_check_container
from yeetus.detector import detect_stack
from yeetus.generator import generate_for_project

pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_DOCKER_BUILD") == "1",
    reason="Docker build and runtime checks disabled by SKIP_DOCKER_BUILD=1",
)

PYPROJECT = '[project]\nname = "example"\nversion = "0.1.0"\nrequires-python = ">=3.12"\ndependencies = []\n'
SERVER = (
    "from http.server import HTTPServer, BaseHTTPRequestHandler\n"
    "class Handler(BaseHTTPRequestHandler):\n"
    "    def do_GET(self):\n"
    "        self.send_response(200)\n"
    "        self.end_headers()\n"
    "        self.wfile.write(b'Hello Python')\n"
    "HTTPServer(('0.0.0.0', 5000), Handler).serve_forever()\n"
)


@pytest.mark.parametrize("level", ["minimal", "full"])
@pytest.mark.parametrize(
    "source", ["pyproject", "uv-lock", "pipfile", "setup", "script"]
)
def test_python_manifest_container(tmp_path, source, level):
    (tmp_path / "app.py").write_text(SERVER)
    if source in ("pyproject", "uv-lock"):
        (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    if source == "uv-lock":
        (tmp_path / "uv.lock").write_text(
            'version = 1\nrevision = 3\nrequires-python = ">=3.12"\n'
            '\n[[package]]\nname = "example"\nversion = "0.1.0"\nsource = { virtual = "." }\n'
        )
    if source == "pipfile":
        (tmp_path / "Pipfile").write_text(
            '[[source]]\nurl = "https://pypi.org/simple"\nverify_ssl = true\nname = "pypi"\n\n[packages]\n'
        )
    if source == "setup":
        (tmp_path / "setup.py").write_text(
            'from setuptools import setup\nsetup(name="example", version="0.1.0", py_modules=["app"])\n'
        )
    generate_for_project(tmp_path, level=level)
    build_and_check_container(
        tmp_path, f"yeetus-test-python-{source}-{level}", 5000, full=level == "full"
    )


@pytest.mark.parametrize("framework,port", [("vite", 5173), ("nextjs", 3000)])
@pytest.mark.parametrize("package_manager", ["pnpm", "yarn", "bun"])
def test_full_node_package_manager_container(
    tmp_path, package_manager, framework, port
):
    shutil.copytree(FIXTURES_DIR / f"node-{framework}", tmp_path, dirs_exist_ok=True)
    package = tmp_path / "package.json"
    data = json.loads(package.read_text())
    versions = {"pnpm": "9.0.0", "yarn": "1.22.22", "bun": "1.4.3"}
    data["packageManager"] = f"{package_manager}@{versions[package_manager]}"
    package.write_text(json.dumps(data))
    generate_for_project(tmp_path, level="full")
    build_and_check_container(
        tmp_path, f"yeetus-test-{framework}-{package_manager}-full", port, full=True
    )


def test_nested_fastapi_pyproject_container(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="example"\nversion="0.1.0"\nrequires-python=">=3.12"\n'
        'dependencies=["fastapi>=0.110.0", "uvicorn>=0.28.0"]\n'
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "api.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n"
        '@app.get("/")\ndef home():\n    return {"message": "Hello nested API"}\n'
    )
    info = detect_stack(tmp_path).with_entrypoint("src/api.py")
    generate_for_project(tmp_path, level="full", stack_info=info)
    build_and_check_container(
        tmp_path, "yeetus-test-nested-fastapi-pyproject", 8000, full=True
    )


@pytest.mark.parametrize("level", ["minimal", "full"])
def test_custom_flask_entrypoint_container(tmp_path, level):
    shutil.copytree(FIXTURES_DIR / "python-flask", tmp_path, dirs_exist_ok=True)
    (tmp_path / "app.py").rename(tmp_path / "server.py")
    info = detect_stack(tmp_path).with_entrypoint("server.py")
    generate_for_project(tmp_path, level=level, stack_info=info)
    build_and_check_container(
        tmp_path, f"yeetus-test-custom-flask-{level}", 5000, full=level == "full"
    )
