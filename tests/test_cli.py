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
