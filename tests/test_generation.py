import os
import shutil
import subprocess

import pytest

from tests.conftest import EXPECTED_DIR, FIXTURES_DIR
from tests.docker_helpers import build_and_check_container
from yeetus.detector import detect_stack
from yeetus.generator import generate_for_project

STACKS = [
    "python-flask",
    "python-fastapi",
    "python-django",
    "node-nextjs",
    "node-react",
    "node-vite",
    "node-vue",
    "static-html",
]

LEVELS = ["minimal", "full"]

PARAMETRIZED_CASES = [(stack, level) for stack in STACKS for level in LEVELS]


@pytest.mark.parametrize("stack,level", PARAMETRIZED_CASES)
def test_generation(stack, level, tmp_path):
    # 1. Copy fixture into tmp_path
    src_fixture = FIXTURES_DIR / stack
    assert src_fixture.exists(), f"Fixture {stack} not found at {src_fixture}"

    for item in src_fixture.iterdir():
        if item.is_dir():
            shutil.copytree(item, tmp_path / item.name)
        else:
            shutil.copy2(item, tmp_path / item.name)

    check_exclusions = stack == "static-html"
    if check_exclusions:
        (tmp_path / ".env").write_text("REVIEW_SECRET=do-not-publish\n")
        for directory in (".git", "node_modules", ".venv"):
            (tmp_path / directory).mkdir()
            (tmp_path / directory / "review-secret").write_text("do-not-publish")
        (tmp_path / "Dockerfile.dockerignore").write_text("# Custom rules\n!.env\n")

    # 2. Run yeetus against it
    generate_for_project(project_dir=tmp_path, level=level, service_name="web")

    # 3. Assert files exist and are non-empty
    expected_snapshot_dir = EXPECTED_DIR / f"{stack}-{level}"
    assert expected_snapshot_dir.exists(), (
        f"Snapshot dir {expected_snapshot_dir} does not exist"
    )

    expected_files = [f.name for f in expected_snapshot_dir.iterdir() if f.is_file()]
    for filename in expected_files:
        gen_file = tmp_path / filename
        assert gen_file.exists(), (
            f"Expected generated file {filename} not found in {tmp_path}"
        )
        assert gen_file.stat().st_size > 0, f"Generated file {filename} is empty"

    # 4. Assert content matches expected snapshot
    for filename in expected_files:
        expected_content = (expected_snapshot_dir / filename).read_text()
        generated_content = (tmp_path / filename).read_text()
        assert generated_content == expected_content, (
            f"Content mismatch for {filename} in {stack}-{level}:\n"
            f"--- EXPECTED ---\n{expected_content}\n"
            f"--- GENERATED ---\n{generated_content}\n"
        )

    # 5. Run `docker compose config` and assert exit 0
    compose_proc = subprocess.run(
        ["docker", "compose", "config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert compose_proc.returncode == 0, (
        f"`docker compose config` failed for {stack}-{level}:\n"
        f"STDOUT: {compose_proc.stdout}\nSTDERR: {compose_proc.stderr}"
    )

    # 6. Build and start the image; poll HTTP and full-mode healthchecks.
    if os.environ.get("SKIP_DOCKER_BUILD") != "1":
        build_and_check_container(
            tmp_path,
            f"yeetus-test-{stack}-{level}",
            detect_stack(tmp_path).port,
            full=level == "full",
            check_exclusions=check_exclusions,
        )
