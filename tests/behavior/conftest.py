"""Behavior test configuration and shared fixtures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the repository root is on the import path so ``tests.conftest`` can be
# imported reliably when running behavior tests directly.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Make the ``features`` package importable so feature files can be targeted by
# their direct paths. This mirrors ``bdd_features_base_dir`` in ``pytest.ini``
# and ensures ``pytest`` resolves paths like
# ``tests/behavior/features/<feature>.feature``.
FEATURES_DIR = Path(__file__).resolve().parent / "features"
FEATURES_PARENT = FEATURES_DIR.parent
if str(FEATURES_PARENT) not in sys.path:
    sys.path.insert(0, str(FEATURES_PARENT))

from autoresearch.api import reset_request_log  # noqa: E402
from autoresearch.config.loader import ConfigLoader  # noqa: E402
from autoresearch.config.models import ConfigModel  # noqa: E402
from autoresearch.orchestration.state import QueryState  # noqa: E402
from autoresearch.storage import StorageContext, StorageManager  # noqa: E402
from tests.conftest import reset_limiter_state, VSS_AVAILABLE  # noqa: E402

pytest_plugins = ("pytest_bdd",)


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Load step modules and configure feature base directory."""
    config.option.bdd_features_base_dir = str(FEATURES_DIR)
    config.pluginmanager.import_plugin("tests.behavior.steps")


@pytest.fixture
def test_context() -> dict:
    """Mutable mapping for sharing state in behavior tests."""
    return {}


@pytest.fixture
def query_state() -> QueryState:
    """Provide a fresh ``QueryState`` instance for each scenario."""
    return QueryState(query="")


@pytest.fixture
def config_model() -> ConfigModel:
    """Provide a fresh ``ConfigModel`` instance for each scenario."""
    return ConfigModel()


@pytest.fixture(autouse=True)
def enable_real_vss(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable real VSS extension only when available."""
    if VSS_AVAILABLE:
        monkeypatch.setenv("REAL_VSS_TEST", "1")
        yield
        monkeypatch.delenv("REAL_VSS_TEST", raising=False)
    else:
        yield


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip VSS-dependent scenarios when the extension is unavailable."""
    if not VSS_AVAILABLE and item.get_closest_marker("requires_vss"):
        pytest.skip("VSS extension not available")


@pytest.fixture(autouse=True)
def reset_api_request_log() -> None:
    """Clear API request log before each scenario."""
    reset_request_log()
    reset_limiter_state()


@pytest.fixture(autouse=True)
def bdd_storage_manager(storage_manager):
    """Use the global temporary storage fixture for behavior tests."""
    yield storage_manager


@pytest.fixture(autouse=True)
def reset_global_state() -> None:
    """Reset ConfigLoader, environment variables, and storage after each scenario."""
    original_env = os.environ.copy()
    ConfigLoader.reset_instance()
    yield
    ConfigLoader.reset_instance()
    StorageManager.context = StorageContext()
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def storage_error_handler():
    """Fixture for handling storage errors in BDD tests.

    This fixture provides methods for attempting operations that might raise
    storage errors and for verifying the error messages.

    Returns:
        A handler object with methods for working with storage errors.
    """

    class StorageErrorHandler:
        def attempt_operation(self, operation, bdd_context, context_key: str = "storage_error"):
            """Attempt an operation that might raise an exception.

            Args:
                operation (callable): The operation to attempt.
                bdd_context (dict): The BDD context dictionary.
                context_key (str): Key used for storing the error in the context.

            Returns:
                The result of the operation if successful, ``None`` otherwise.
            """

            from autoresearch.errors import StorageError  # noqa: WPS433

            try:
                result = operation()
            except StorageError as exc:  # pragma: no cover - defensive
                bdd_context[context_key] = str(exc)
                return None
            else:  # pragma: no cover - defensive
                return result

    return StorageErrorHandler()
