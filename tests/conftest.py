from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
EXPECTED_DIR = TESTS_DIR / "expected"

@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR

@pytest.fixture
def expected_dir():
    return EXPECTED_DIR
