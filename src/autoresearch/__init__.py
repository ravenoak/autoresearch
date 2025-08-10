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
from importlib.metadata import version as _version

try:  # pragma: no cover - best effort patch
    module = importlib.import_module("pydantic.root_model")
    sys.modules.setdefault("pydantic.root_model", module)
except Exception:  # pragma: no cover
    pass

__version__ = _version("autoresearch")

try:  # pragma: no cover - optional distributed extras
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
except Exception as exc:  # pragma: no cover - missing optional deps
    ProcessExecutor = None  # type: ignore
    RayExecutor = None  # type: ignore
    StorageCoordinator = None  # type: ignore
    ResultAggregator = None  # type: ignore
    InMemoryBroker = None  # type: ignore
    RedisBroker = None  # type: ignore
    start_storage_coordinator = None  # type: ignore
    start_result_aggregator = None  # type: ignore
    publish_claim = None  # type: ignore
    import warnings

    warnings.warn(f"Distributed features unavailable: {exc}")

__all__ = [
    "__version__",
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
