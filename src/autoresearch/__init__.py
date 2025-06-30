"""Autoresearch package initialization.

This package provides a local-first research assistant with multiple
interfaces and a modular architecture.
"""

from .distributed import (
    RayExecutor,
    StorageCoordinator,
    InMemoryBroker,
    start_storage_coordinator,
    publish_claim,
)

__all__ = [
    "RayExecutor",
    "StorageCoordinator",
    "InMemoryBroker",
    "start_storage_coordinator",
    "publish_claim",
]
