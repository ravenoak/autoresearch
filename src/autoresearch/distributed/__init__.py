"""Distributed execution utilities.

See docs/algorithms/distributed_coordination.md for mathematical models.
"""

from typing import TYPE_CHECKING

from .broker import (
    InMemoryBroker,
    RedisBroker,
    RedisQueue,
    BrokerType,
    get_message_broker,
)
from .coordinator import (
    StorageCoordinator,
    ResultAggregator,
    start_storage_coordinator,
    start_result_aggregator,
    publish_claim,
)
# Lazy-loaded exports are declared as strings to avoid eager imports that
# would otherwise create circular dependencies during module initialisation.
__all__ = [
    "InMemoryBroker",
    "RedisBroker",
    "RedisQueue",
    "BrokerType",
    "get_message_broker",
    "StorageCoordinator",
    "ResultAggregator",
    "start_storage_coordinator",
    "start_result_aggregator",
    "publish_claim",
    "RayExecutor",
    "ProcessExecutor",
]


def __getattr__(name: str) -> object:
    """Lazily import executor classes on demand."""

    if name in {"RayExecutor", "ProcessExecutor"}:
        from . import executors as _executors

        return getattr(_executors, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:  # pragma: no cover - import-time only for static analysis
    from .executors import ProcessExecutor, RayExecutor
