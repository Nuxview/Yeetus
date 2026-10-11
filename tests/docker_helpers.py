import json
import subprocess
import time
import urllib.error
import urllib.request


def docker(*args):
    result = subprocess.run(
        ["docker", *args], capture_output=True, text=True, check=True, timeout=600
    )
    output = result.stdout + result.stderr if args[0] == "logs" else result.stdout
    return output.strip()


def build_and_check_container(
    project_dir, image, port, full=False, check_exclusions=False
):
    proc = subprocess.run(
        ["docker", "build", "-t", image, "."],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=1200,
    )
    assert proc.returncode == 0, f"Docker build failed:\n{proc.stdout}\n{proc.stderr}"
    args = [
        "run",
        "--detach",
        "--label",
        "yeetus.test=true",
        "--publish",
        f"127.0.0.1::{port}",
    ]
    if full:
        args.extend(["--health-interval", "1s", "--health-start-period", "1s"])
    container = docker(*args, image)
    try:
        binding = docker("port", container, f"{port}/tcp").splitlines()[0]
        url = f"http://{binding}/"
        http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        deadline = time.monotonic() + 90
        last_error = "Server did not become ready"
        while time.monotonic() < deadline:
            state = json.loads(
                docker("inspect", "--format", "{{json .State}}", container)
            )
            assert state["Running"], (
                f"Container exited:\n{docker('logs', '--tail', '20', container)}"
            )
            try:
                with http.open(url, timeout=2) as response:
                    assert response.status == 200
                if not full or state.get("Health", {}).get("Status") == "healthy":
                    break
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                last_error = str(exc)
            time.sleep(0.5)
        else:
            raise AssertionError(
                f"Container did not become healthy: {last_error}\n{docker('logs', '--tail', '20', container)}\n{state}"
            )

        if check_exclusions:
            # Verify actual image contents, including a Dockerfile-specific ignore.
            root = "/usr/share/nginx/html"
            docker(
                "exec",
                container,
                "sh",
                "-c",
                f"test ! -e {root}/.env && test ! -e {root}/.git && test ! -e {root}/node_modules && test ! -e {root}/.venv",
            )
            for secret_path in [".env", ".git/review-secret"]:
                try:
                    with http.open(url + secret_path, timeout=2):
                        pass
                except urllib.error.HTTPError as exc:
                    assert exc.code == 404
                else:
                    raise AssertionError(f"Static container exposed {secret_path}")
    finally:
        docker("rm", "--force", container)
