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
