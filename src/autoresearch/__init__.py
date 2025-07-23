"""Autoresearch package initialization.

This package provides a local-first research assistant with multiple
interfaces and a modular architecture.
"""

__version__ = "0.1.0"

try:  # pragma: no cover - optional distributed extras
    from .distributed import (
        ProcessExecutor,
        RayExecutor,
        StorageCoordinator,
        ResultAggregator,
        InMemoryBroker,
        RedisBroker,
        start_storage_coordinator,
        start_result_aggregator,
        publish_claim,
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
