import json
import os
import shutil
import subprocess

import pytest
from typer.testing import CliRunner

from yeetus.cli import app
from yeetus.detector import detect_stack
from yeetus.generator import Generator, generate_for_project
from yeetus.models import ProjectPart


@pytest.mark.parametrize("level", ["minimal", "full"])
def test_flask_custom_entrypoint_is_in_command(tmp_path, level):
    (tmp_path / "requirements.txt").write_text("flask\n")
    (tmp_path / "server.py").write_text(
        "from flask import Flask\napp = Flask(__name__)\n"
    )
    result = CliRunner().invoke(
        app,
        ["init", str(tmp_path), "--level", level, "--entrypoint", "server.py"],
        input="y\n",
    )
    assert result.exit_code == 0, result.output
    command = json.loads((tmp_path / "Dockerfile").read_text().split("CMD ")[-1])
    assert command[command.index("--app") + 1] == "server.py"


def test_fastapi_nested_entrypoint_preserves_module_path(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
    info = detect_stack(tmp_path).with_entrypoint("src/api.py")
    assert json.loads(info.cmd)[1] == "src.api:app"


@pytest.mark.parametrize("force", [False, True])
def test_readme_overwrite_requires_confirmation(tmp_path, force):
    (tmp_path / "index.html").write_text("hello")
    readme = tmp_path / "README.docker.md"
    readme.write_text("Existing deployment notes\n")
    args = ["init", str(tmp_path), "--level", "minimal"]
    if force:
        args.append("--force")
    result = CliRunner().invoke(app, args, input="y\nn\n")
    if force:
        assert result.exit_code == 0, result.output
        assert "Services" in readme.read_text()
    else:
        assert result.exit_code != 0
        assert readme.read_text() == "Existing deployment notes\n"
        assert not (tmp_path / "Dockerfile").exists()


def test_duplicate_service_names_are_rejected_before_writes(tmp_path):
    parts = []
    for subdir, port in [("frontend", 8080), ("backend", 8081)]:
        path = tmp_path / subdir
        path.mkdir()
        (path / "index.html").write_text("hello")
        parts.append(
            ProjectPart("web", path, detect_stack(path), port=port, target_port=80)
        )
    with pytest.raises(ValueError, match="Duplicate service name"):
        Generator().generate(tmp_path, parts)
    assert not (tmp_path / "compose.yaml").exists()
    assert not any(tmp_path.rglob("Dockerfile"))


def test_compose_paths_survive_yaml(tmp_path):
    path = tmp_path / "web #1: 'quoted'"
    path.mkdir()
    (path / "index.html").write_text("hello")
    Generator().generate(
        tmp_path, [ProjectPart("web", path, detect_stack(path), level="full")]
    )
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json", "--no-env-resolution"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    service = json.loads(result.stdout)["services"]["web"]
    assert service["build"]["context"] == str(path)
    assert service["env_file"][0]["path"] == str(path / ".env")


def test_dockerignore_preserves_custom_rules_and_is_idempotent(tmp_path):
    (tmp_path / "index.html").write_text("hello")
    ignore = tmp_path / ".dockerignore"
    ignore.write_text("large-assets/\n!.env\n")
    # Dockerfile-specific ignores override the root .dockerignore.
    specific = tmp_path / "Dockerfile.dockerignore"
    specific.write_text("other-assets/\n!.env\n")
    files = generate_for_project(tmp_path)
    for file in (ignore, specific):
        assert file in files
        content = file.read_text()
        assert "assets/" in content
        assert content.index("!.env") < content.index("**/.env")
        assert "**/.git" in content
        assert "**/node_modules" in content
        assert "**/.venv" in content
    before = (ignore.read_text(), specific.read_text())
    generate_for_project(tmp_path)
    assert (ignore.read_text(), specific.read_text()) == before


def test_dry_run_does_not_modify_dockerignore(tmp_path):
    (tmp_path / "index.html").write_text("hello")
    ignore = tmp_path / ".dockerignore"
    ignore.write_text("my-rule\n")
    files = generate_for_project(tmp_path, dry_run=True)
    assert ignore in files
    assert ignore.read_text() == "my-rule\n"
    assert not (tmp_path / "Dockerfile").exists()


@pytest.mark.parametrize("level", ["minimal", "full"])
@pytest.mark.parametrize(
    "manifest,contents,install",
    [
        ("pyproject.toml", '[project]\nname="example"\nversion="0.1"\n', "uv sync"),
        ("Pipfile", "[packages]\n", "pipenv install --system"),
        (
            "setup.py",
            'from setuptools import setup\nsetup(name="example")\n',
            "pip install --no-cache-dir .",
        ),
        ("app.py", 'print("hello")\n', None),
    ],
)
def test_python_installation_matches_manifest(
    tmp_path, level, manifest, contents, install
):
    (tmp_path / manifest).write_text(contents)
    generate_for_project(tmp_path, level=level)
    dockerfile = (tmp_path / "Dockerfile").read_text()
    assert "requirements.txt" not in dockerfile
    if install:
        assert install in dockerfile
    else:
        assert "RUN pip install" not in dockerfile


def test_uv_lock_uses_locked_sync(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="example"\nversion="0.1"\n'
    )
    (tmp_path / "uv.lock").write_text("version = 1\n")
    generate_for_project(tmp_path)
    assert "uv sync --locked" in (tmp_path / "Dockerfile").read_text()


def test_orphan_uv_lock_fails_before_writing(tmp_path):
    (tmp_path / "uv.lock").write_text("version = 1\n")
    with pytest.raises(ValueError, match="pyproject.toml"):
        generate_for_project(tmp_path)
    assert not (tmp_path / "Dockerfile").exists()


def test_full_node_install_keeps_dev_tools(tmp_path):
    if not shutil.which("npm"):
        pytest.skip("npm is required for the offline dependency installation probe")
    tool = tmp_path / "dev-tool"
    tool.mkdir()
    (tool / "package.json").write_text(
        json.dumps({"name": "vite", "version": "1.0.0", "bin": {"vite": "index.js"}})
    )
    (tool / "index.js").write_text(
        '#!/usr/bin/env node\nconsole.log("dev tool available")\n'
    )
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "example",
                "scripts": {"dev": "vite"},
                "devDependencies": {"vite": "file:./dev-tool"},
            }
        )
    )
    generate_for_project(tmp_path, level="full")
    env = dict(os.environ, npm_config_cache=str(tmp_path / "npm-cache"))
    env.pop("NODE_ENV", None)
    # Execute npm with the environment active at the generated install step.
    for line in (tmp_path / "Dockerfile").read_text().splitlines():
        if line.startswith("ENV NODE_ENV="):
            env["NODE_ENV"] = line.split("=", 1)[1]
        if line == "RUN npm install":
            subprocess.run(
                [
                    "npm",
                    "install",
                    "--offline",
                    "--ignore-scripts",
                    "--no-audit",
                    "--no-fund",
                ],
                cwd=tmp_path,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            break
    result = subprocess.run(
        json.loads(detect_stack(tmp_path).cmd),
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "dev tool available" in result.stdout


@pytest.mark.parametrize("level", ["minimal", "full"])
@pytest.mark.parametrize(
    "declaration,version",
    [
        ("pnpm@9.0.0+sha224.example", "9.0.0"),
        ("pnpm@invalid;echo injected", "9"),
        (None, "9"),
    ],
)
def test_pnpm_installation_uses_validated_version(
    tmp_path, level, declaration, version
):
    package = {"name": "example", "dependencies": {"vite": "^5.2.0"}}
    if declaration:
        package["packageManager"] = declaration
    (tmp_path / "package.json").write_text(json.dumps(package))
    (tmp_path / "pnpm-workspace.yaml").write_text(
        "onlyBuiltDependencies:\n  - esbuild\n"
    )
    generate_for_project(tmp_path, level=level)
    dockerfile = (tmp_path / "Dockerfile").read_text()
    assert f"RUN npm install -g pnpm@{version}\n" in dockerfile
    assert "echo injected" not in dockerfile
    if level == "full":
        assert (
            "COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* .pnpmfile.cjs* ./"
            in dockerfile
        )
