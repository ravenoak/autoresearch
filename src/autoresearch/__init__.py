"""Autoresearch package initialization.

This package provides a local-first research assistant with multiple
interfaces and a modular architecture.
"""

# Ensure compatibility with libraries that expect ``pydantic.root_model`` to be
# loaded (e.g. ``a2a-sdk`` with Pydantic 2). Explicitly import the module and
# register it in ``sys.modules`` to avoid `KeyError` issues during model
# creation.
import importlib
import sys
from importlib.metadata import PackageNotFoundError, version as _version
from typing import TYPE_CHECKING
import warnings

try:  # pragma: no cover - best effort patch
    module = importlib.import_module("pydantic.root_model")
    sys.modules.setdefault("pydantic.root_model", module)
except Exception:  # pragma: no cover
    pass

try:
    __version__ = _version("autoresearch")
except PackageNotFoundError:  # pragma: no cover - fallback for tests
    __version__ = "0.1.0a1"

# Keep release metadata aligned with pyproject.toml and CHANGELOG.md.
__release_date__ = "2025-10-08"

if TYPE_CHECKING:  # pragma: no cover - import for type checkers only
    from .distributed import (
        InMemoryBroker,
        ProcessExecutor,
        RayExecutor,
        RedisBroker,
        ResultAggregator,
        StorageCoordinator,
        publish_claim,
        start_result_aggregator,
        start_storage_coordinator,
    )

__all__ = [
    "__version__",
    "__release_date__",
    "RayExecutor",
    "ProcessExecutor",
    "StorageCoordinator",
    "ResultAggregator",
    "InMemoryBroker",
    "RedisBroker",
    "start_storage_coordinator",
    "start_result_aggregator",
    "publish_claim",
]

_DISTRIBUTED_ATTRS = {
    "RayExecutor",
    "ProcessExecutor",
    "StorageCoordinator",
    "ResultAggregator",
    "InMemoryBroker",
    "RedisBroker",
    "start_storage_coordinator",
    "start_result_aggregator",
    "publish_claim",
}


def __getattr__(name: str) -> object:
    """Lazily import distributed features on first access."""
    if name in _DISTRIBUTED_ATTRS:
        try:  # pragma: no cover - optional distributed extras
            module = importlib.import_module(".distributed", __name__)
        except Exception as exc:  # pragma: no cover - missing optional deps
            warnings.warn(f"Distributed features unavailable: {exc}")
            raise AttributeError(name) from exc
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(name)
