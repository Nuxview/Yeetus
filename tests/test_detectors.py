from tests.conftest import FIXTURES_DIR
from yeetus.detector import detect_stack


def test_detect_python_flask():
    stack_info = detect_stack(FIXTURES_DIR / "python-flask")
    assert stack_info is not None
    assert stack_info.stack_type == "python"
    assert stack_info.framework == "flask"
    assert stack_info.port == 5000


def test_detect_python_fastapi():
    stack_info = detect_stack(FIXTURES_DIR / "python-fastapi")
    assert stack_info is not None
    assert stack_info.stack_type == "python"
    assert stack_info.framework == "fastapi"
    assert stack_info.port == 8000


def test_detect_python_django():
    stack_info = detect_stack(FIXTURES_DIR / "python-django")
    assert stack_info is not None
    assert stack_info.stack_type == "python"
    assert stack_info.framework == "django"
    assert stack_info.port == 8000


def test_detect_node_nextjs():
    stack_info = detect_stack(FIXTURES_DIR / "node-nextjs")
    assert stack_info is not None
    assert stack_info.stack_type == "node"
    assert stack_info.framework == "nextjs"
    assert stack_info.port == 3000


def test_detect_node_react():
    stack_info = detect_stack(FIXTURES_DIR / "node-react")
    assert stack_info is not None
    assert stack_info.stack_type == "node"
    assert stack_info.framework == "react"
    assert stack_info.port == 3000


def test_detect_node_vite():
    stack_info = detect_stack(FIXTURES_DIR / "node-vite")
    assert stack_info is not None
    assert stack_info.stack_type == "node"
    assert stack_info.framework == "vite"
    assert stack_info.port == 5173


def test_detect_node_vue():
    stack_info = detect_stack(FIXTURES_DIR / "node-vue")
    assert stack_info is not None
    assert stack_info.stack_type == "node"
    assert stack_info.framework == "vue"
    assert stack_info.port == 8080


def test_detect_static_html():
    stack_info = detect_stack(FIXTURES_DIR / "static-html")
    assert stack_info is not None
    assert stack_info.stack_type == "static"
    assert stack_info.framework == "static"
    assert stack_info.port == 80


def test_detect_empty_dir(tmp_path):
    assert detect_stack(tmp_path) is None


def test_detect_node_pnpm(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"name": "test", "dependencies": {"next": "14.0.0"}}'
    )
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '6.0'")
    stack_info = detect_stack(tmp_path)
    assert stack_info is not None
    assert stack_info.package_manager == "pnpm"
    assert '["pnpm", "start"]' in stack_info.cmd
    assert "[pnpm]" in stack_info.description


def test_detect_node_yarn(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"name": "test", "dependencies": {"react": "18.0.0"}}'
    )
    (tmp_path / "yarn.lock").write_text("# yarn lockfile v1")
    stack_info = detect_stack(tmp_path)
    assert stack_info is not None
    assert stack_info.package_manager == "yarn"
    assert '["yarn", "start"]' in stack_info.cmd
    assert "[yarn]" in stack_info.description


def test_detect_node_bun(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"name": "test", "devDependencies": {"vite": "5.0.0"}}'
    )
    (tmp_path / "bun.lockb").write_text("")
    stack_info = detect_stack(tmp_path)
    assert stack_info is not None
    assert stack_info.package_manager == "bun"
    assert '["bun", "run", "dev", "--host"]' in stack_info.cmd
    assert "[bun]" in stack_info.description


def test_detect_node_package_manager_field(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"name": "test", "packageManager": "pnpm@9.0.0", "dependencies": {"vue": "3.0.0"}}'
    )
    stack_info = detect_stack(tmp_path)
    assert stack_info is not None
    assert stack_info.package_manager == "pnpm"
    assert '["pnpm", "run", "serve"]' in stack_info.cmd


def test_detect_python_entrypoints():
    flask_info = detect_stack(FIXTURES_DIR / "python-flask")
    assert flask_info.entrypoint == "app.py"

    fastapi_info = detect_stack(FIXTURES_DIR / "python-fastapi")
    assert fastapi_info.entrypoint == "main.py"

    django_info = detect_stack(FIXTURES_DIR / "python-django")
    assert django_info.entrypoint == "manage.py"


def test_detect_python_generic(tmp_path):
    (tmp_path / "script.py").write_text("print('hello')")
    info = detect_stack(tmp_path)
    assert info is not None
    assert info.stack_type == "python"
    assert info.framework == "python"
    assert info.description == "Python Generic"

    # with_entrypoint preserves generic command instead of flask
    custom_info = info.with_entrypoint("worker.py")
    assert custom_info.cmd == '["python", "worker.py"]'
    assert "flask" not in custom_info.cmd.lower()


def test_detect_node_with_python_helper_script(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"name": "node-app", "dependencies": {"next": "14.0.0"}}'
    )
    (tmp_path / "helper.py").write_text("# Python helper script")
    info = detect_stack(tmp_path)
    assert info is not None
    assert info.stack_type == "node"
    assert info.framework == "nextjs"
