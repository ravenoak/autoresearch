import sys
from pathlib import Path

# Ensure package can be imported without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import pytest
from autoresearch.config import ConfigLoader


@pytest.fixture(autouse=True)
def stop_config_watcher():
    """Ensure ConfigLoader watcher threads are cleaned up."""
    yield
    ConfigLoader().stop_watching()


@pytest.fixture
def bdd_context():
    """Mutable mapping for sharing data between BDD steps."""
    return {}
