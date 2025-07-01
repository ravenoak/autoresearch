"""Autoresearch package initialization.

This package provides a local-first research assistant with multiple
interfaces and a modular architecture.
"""

from .distributed import (
    ProcessExecutor,
    RayExecutor,
    StorageCoordinator,
    ResultAggregator,
    InMemoryBroker,
    start_storage_coordinator,
    start_result_aggregator,
    publish_claim,
)

__all__ = [
    "RayExecutor",
    "ProcessExecutor",
    "StorageCoordinator",
    "ResultAggregator",
    "InMemoryBroker",
    "start_storage_coordinator",
    "start_result_aggregator",
    "publish_claim",
]
