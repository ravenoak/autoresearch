import sys
from pathlib import Path

# Ensure package can be imported without installation
src_path = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_path))  # noqa: E402

import pytest  # noqa: E402
from autoresearch.config import ConfigLoader  # noqa: E402


@pytest.fixture(autouse=True)
def stop_config_watcher():
    """Ensure ConfigLoader watcher threads are cleaned up."""
    yield
    ConfigLoader().stop_watching()


@pytest.fixture
def bdd_context():
    """Mutable mapping for sharing data between BDD steps."""
    return {}
