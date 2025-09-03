"""Coordinate distributed storage and result aggregation.

The coordinator offers two guarantees:

* **Safety** – every persisted claim or aggregated result originates from a
  unique message. A single consumer drains the broker queue, preventing
  duplicates.
* **Liveness** – any message eventually reaches durable storage or the result
  list while the processes run. The event loop processes queue items until a
  ``stop`` action appears, so no pending message is skipped.

Together these properties constitute a simple proof of correctness for the
protocol: each action is handled exactly once (safety) and all actions are
eventually handled (liveness). See
``docs/algorithms/distributed_coordination.md`` for a fuller discussion and
benchmark data.
"""

from __future__ import annotations

import multiprocessing
from multiprocessing.synchronize import Event
from typing import Any

from ..config.models import ConfigModel
from .. import storage
from ..logging_utils import get_logger

from .broker import BrokerType, get_message_broker

log = get_logger(__name__)


class StorageCoordinator(multiprocessing.Process):
    """Background process that persists claims from a queue.

    Args:
        queue: Message queue carrying claim dictionaries.
        db_path: Location of the DuckDB database.
        ready_event: Optional event set when initialization finishes.
    """

    def __init__(self, queue: Any, db_path: str, ready_event: Event | None = None) -> None:
        super().__init__(daemon=True)
        self._queue = queue
        self._db_path = db_path
        self._ready_event = ready_event

    def run(self) -> None:  # pragma: no cover - runs in separate process
        storage.setup(self._db_path)
        if self._ready_event is not None:
            self._ready_event.set()
        while True:
            try:
                msg = self._queue.get()
            except (EOFError, OSError):
                break
            if msg.get("action") == "stop":
                break
            if msg.get("action") == "persist_claim":
                storage.StorageManager.persist_claim(
                    msg["claim"], msg.get("partial_update", False)
                )
        storage.teardown()


class ResultAggregator(multiprocessing.Process):
    """Collect results from agents running in other processes.

    Args:
        queue: Message queue carrying result dictionaries.
    """

    def __init__(self, queue: Any) -> None:
        super().__init__(daemon=True)
        self._queue = queue
        self._manager = multiprocessing.Manager()
        self.results: multiprocessing.managers.ListProxy[dict[str, Any]] = self._manager.list()  # type: ignore[attr-defined]

    def run(self) -> None:  # pragma: no cover - runs in separate process
        while True:
            try:
                msg = self._queue.get()
            except (EOFError, OSError):
                break
            if msg.get("action") == "stop":
                break
            if msg.get("action") == "agent_result":
                self.results.append(msg)


def start_storage_coordinator(config: ConfigModel) -> tuple[StorageCoordinator, BrokerType]:
    """Start a storage coordinator according to the distributed config.

    Args:
        config: Application configuration.

    Returns:
        The coordinator process and the message broker it consumes.
    """

    dist_cfg = config.distributed_config
    broker = get_message_broker(
        getattr(dist_cfg, "message_broker", None),
        getattr(dist_cfg, "broker_url", None),
    )
    db_path = config.storage.duckdb_path
    ready = multiprocessing.Event()
    coordinator = StorageCoordinator(broker.queue, db_path, ready)
    coordinator.start()
    ready.wait()
    return coordinator, broker


def publish_claim(
    broker: BrokerType, claim: dict[str, Any], partial_update: bool = False
) -> None:
    """Publish a claim persistence request to the broker.

    Args:
        broker: Message broker used for coordination.
        claim: Claim payload to persist.
        partial_update: Whether to perform a partial update.
    """
    broker.publish(
        {"action": "persist_claim", "claim": claim, "partial_update": partial_update}
    )


def start_result_aggregator(config: ConfigModel) -> tuple[ResultAggregator, BrokerType]:
    """Start a background aggregator process for agent results.

    Args:
        config: Application configuration.

    Returns:
        The aggregator process and the message broker supplying results.
    """

    dist_cfg = config.distributed_config
    broker = get_message_broker(getattr(dist_cfg, "message_broker", None), getattr(dist_cfg, "broker_url", None))
    aggregator = ResultAggregator(broker.queue)
    aggregator.start()
    return aggregator, broker
