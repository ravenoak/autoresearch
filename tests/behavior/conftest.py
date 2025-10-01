"""Behavior test configuration and shared fixtures."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

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
from tests.typing_helpers import TypedFixture

T_co = TypeVar("T_co", covariant=True)


class StorageErrorHandler:
    """Helper for capturing storage errors raised within steps."""

    def attempt_operation(
        self,
        operation: Callable[[], T_co],
        bdd_context: dict[str, object],
        context_key: str = "storage_error",
    ) -> T_co | None:
        """Attempt an operation that might raise an exception."""

        from autoresearch.errors import StorageError  # noqa: WPS433

        try:
            return operation()
        except StorageError as exc:  # pragma: no cover - defensive
            bdd_context[context_key] = str(exc)
            return None

# Load fixtures and step implementations so their fixtures are available
pytest_plugins = (
    "pytest_bdd",
    "tests.behavior.fixtures",
    "tests.behavior.steps",
)


ALLOWED_STEP_MODULES = {
    "agent_orchestration_steps.py",
    "circuit_breaker_recovery_steps.py",
    "config_cli_steps.py",
    "evaluation_steps.py",
    "error_recovery_basic_steps.py",
    "error_recovery_redis_steps.py",
    "parallel_group_merging_steps.py",
    "query_interface_steps.py",
    "visualization_cli_steps.py",
    "reasoning_modes_all_steps.py",
    "reasoning_modes_auto_steps.py",
    "reasoning_modes_auto_cli_cycle_steps.py",
    "reasoning_modes_steps.py",
}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip step modules that are not yet implemented."""
    for item in items:
        basename = item.fspath.basename
        if basename.endswith("_steps.py") and basename not in ALLOWED_STEP_MODULES:
            item.add_marker(pytest.mark.skip(reason="scenario not implemented"))


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configure base directory for feature files."""
    config.option.bdd_features_base_dir = str(FEATURES_DIR)


@pytest.fixture
def test_context() -> TypedFixture[dict[str, object]]:
    """Mutable mapping for sharing state in behavior tests."""
    return {}


@pytest.fixture
def query_state() -> TypedFixture[QueryState]:
    """Provide a fresh ``QueryState`` instance for each scenario."""
    return QueryState(query="")


@pytest.fixture
def config_model() -> TypedFixture[ConfigModel]:
    """Provide a fresh ``ConfigModel`` instance for each scenario."""
    return ConfigModel()


@pytest.fixture(autouse=True)
def enable_real_vss(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[None]:
    """Enable real VSS extension only when available."""
    if VSS_AVAILABLE:
        monkeypatch.setenv("REAL_VSS_TEST", "1")
        yield None
        monkeypatch.delenv("REAL_VSS_TEST", raising=False)
    else:
        yield None
    return None


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip VSS-dependent scenarios when the extension is unavailable."""
    if not VSS_AVAILABLE and item.get_closest_marker("requires_vss"):
        pytest.skip("VSS extension not available")


@pytest.fixture(autouse=True)
def reset_api_request_log() -> TypedFixture[None]:
    """Clear API request log before each scenario."""
    reset_request_log()
    reset_limiter_state()
    return None


@pytest.fixture(autouse=True)
def bdd_storage_manager(
    storage_manager: StorageManager,
) -> TypedFixture[StorageManager]:
    """Use the global temporary storage fixture for behavior tests."""
    yield storage_manager
    return None


@pytest.fixture(autouse=True)
def reset_global_state() -> TypedFixture[None]:
    """Reset ConfigLoader, environment variables, and storage after each scenario."""
    original_env = os.environ.copy()
    ConfigLoader.reset_instance()
    yield None
    ConfigLoader.reset_instance()
    StorageManager.context = StorageContext()
    os.environ.clear()
    os.environ.update(original_env)
    return None


@pytest.fixture
def storage_error_handler() -> TypedFixture[StorageErrorHandler]:
    """Provide a helper object for verifying storage exceptions in steps."""

    return StorageErrorHandler()
