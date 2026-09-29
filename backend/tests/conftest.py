import sys
from pathlib import Path

import pytest

# Put backend/ on sys.path so the `app` package can be imported
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.engine.ruleset import load_ruleset  # noqa: E402


@pytest.fixture(scope="session")
def rs() -> dict:
    return load_ruleset()