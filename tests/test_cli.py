import shutil

from typer.testing import CliRunner

from tests.conftest import FIXTURES_DIR
from yeetus import __version__
from yeetus.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_help():
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "--level" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--no-detection" in result.stdout


def test_cli_init_minimal(tmp_path):
    # Copy python-flask fixture into tmp_path
    for item in (FIXTURES_DIR / "python-flask").iterdir():
        if item.is_file():
            shutil.copy2(item, tmp_path / item.name)

    result = runner.invoke(
        app, ["init", str(tmp_path), "--level", "minimal", "--no-readme"]
    )
    assert result.exit_code == 0
    assert (tmp_path / "Dockerfile").exists()
    assert (tmp_path / "compose.yaml").exists()
    assert not (tmp_path / ".env.example").exists()


def test_cli_init_full(tmp_path):
    for item in (FIXTURES_DIR / "python-fastapi").iterdir():
        if item.is_file():
            shutil.copy2(item, tmp_path / item.name)

    result = runner.invoke(
        app, ["init", str(tmp_path), "--level", "full", "--no-readme"]
    )
    assert result.exit_code == 0
    assert (tmp_path / "Dockerfile").exists()
    assert (tmp_path / "compose.yaml").exists()
    assert (tmp_path / ".env.example").exists()


def test_cli_dry_run(tmp_path):
    for item in (FIXTURES_DIR / "static-html").iterdir():
        if item.is_file():
            shutil.copy2(item, tmp_path / item.name)

    result = runner.invoke(
        app, ["init", str(tmp_path), "--level", "minimal", "--dry-run"]
    )
    assert result.exit_code == 0
    assert not (tmp_path / "Dockerfile").exists()
    assert not (tmp_path / "compose.yaml").exists()
    assert "Dry Run Preview" in result.stdout


def test_cli_conflict_abort_and_force(tmp_path):
    for item in (FIXTURES_DIR / "static-html").iterdir():
        if item.is_file():
            shutil.copy2(item, tmp_path / item.name)

    (tmp_path / "Dockerfile").write_text("EXISTING")

    # Abort when prompt says overwrite? (default: No)
    result = runner.invoke(
        app, ["init", str(tmp_path), "--level", "minimal"], input="n\n"
    )
    assert result.exit_code != 0
    assert (tmp_path / "Dockerfile").read_text() == "EXISTING"

    # Overwrite when --force is used
    result_force = runner.invoke(
        app, ["init", str(tmp_path), "--level", "minimal", "--force"]
    )
    assert result_force.exit_code == 0
    assert (tmp_path / "Dockerfile").read_text() != "EXISTING"


def test_cli_python_entrypoint_prompt_default(tmp_path):
    for item in (FIXTURES_DIR / "python-flask").iterdir():
        if item.is_file():
            shutil.copy2(item, tmp_path / item.name)

    # User confirms stack (y) and presses Enter on entrypoint prompt (\n)
    result = runner.invoke(
        app, ["init", str(tmp_path), "--level", "full", "--no-readme"], input="y\n\n"
    )
    assert result.exit_code == 0
    assert "FLASK_APP=app.py" in (tmp_path / ".env.example").read_text()


def test_cli_python_entrypoint_prompt_custom(tmp_path):
    for item in (FIXTURES_DIR / "python-flask").iterdir():
        if item.is_file():
            shutil.copy2(item, tmp_path / item.name)

    # User confirms stack (y) and inputs server.py
    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--level", "full", "--no-readme"],
        input="y\nserver.py\n",
    )
    assert result.exit_code == 0
    assert "FLASK_APP=server.py" in (tmp_path / ".env.example").read_text()


def test_cli_python_entrypoint_option(tmp_path):
    for item in (FIXTURES_DIR / "python-fastapi").iterdir():
        if item.is_file():
            shutil.copy2(item, tmp_path / item.name)

    result = runner.invoke(
        app,
        [
            "init",
            str(tmp_path),
            "--level",
            "minimal",
            "--entrypoint",
            "api_server.py",
            "--no-readme",
        ],
        input="y\n",
    )
    assert result.exit_code == 0
    df_content = (tmp_path / "Dockerfile").read_text()
    assert (
        'CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]'
        in df_content
    )


def test_cli_node_package_managers(tmp_path):
    pnpm_dir = tmp_path / "pnpm_app"
    pnpm_dir.mkdir()
    (pnpm_dir / "package.json").write_text(
        '{"name": "pnpm-app", "dependencies": {"next": "14.0.0"}}'
    )
    (pnpm_dir / "pnpm-lock.yaml").write_text("")

    result = runner.invoke(
        app, ["init", str(pnpm_dir), "--level", "minimal", "--no-readme"], input="y\n"
    )
    assert result.exit_code == 0
    df = (pnpm_dir / "Dockerfile").read_text()
    assert "RUN pnpm install" in df
    assert 'CMD ["pnpm", "start"]' in df

    bun_dir = tmp_path / "bun_app"
    bun_dir.mkdir()
    (bun_dir / "package.json").write_text(
        '{"name": "bun-app", "dependencies": {"next": "14.0.0"}}'
    )
    (bun_dir / "bun.lockb").write_text("")

    result = runner.invoke(
        app, ["init", str(bun_dir), "--level", "minimal", "--no-readme"], input="y\n"
    )
    assert result.exit_code == 0
    df = (bun_dir / "Dockerfile").read_text()
    assert "FROM oven/bun:1-alpine" in df
    assert "RUN bun install" in df


def test_cli_multi_service_custom_port(tmp_path):
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    (web_dir / "package.json").write_text(
        '{"name": "web", "dependencies": {"next": "14.0.0"}}'
    )

    # Prompts:
    # 1. service name -> web
    # 2. subpath -> web
    # 3. use detected stack -> y
    # 4. port -> 8080 (custom host port, internal is 3000)
    # 5. add another service? -> n
    user_input = "web\nweb\ny\n8080\nn\n"
    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--multi", "--level", "minimal", "--no-readme"],
        input=user_input,
    )
    assert result.exit_code == 0
    # Internal Dockerfile should expose target port 3000
    df = (web_dir / "Dockerfile").read_text()
    assert "EXPOSE 3000" in df

    # Compose should map host_port:target_port -> 8080:3000
    compose = (tmp_path / "compose.yaml").read_text()
    assert '"8080:3000"' in compose
