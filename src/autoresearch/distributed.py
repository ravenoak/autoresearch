"""Utilities for distributed agent execution using Ray."""

from __future__ import annotations

from typing import Dict, Callable, Any, Optional
import os
import multiprocessing

from multiprocessing.queues import Queue

from . import storage

import ray

from .config import ConfigModel
from .orchestration.state import QueryState
from .orchestration.orchestrator import AgentFactory
from .models import QueryResponse


class InMemoryBroker:
    """Simple in-memory message broker using multiprocessing.Queue."""

    def __init__(self) -> None:
        self._manager = multiprocessing.Manager()
        self.queue: Queue = self._manager.Queue()

    def publish(self, message: dict[str, Any]) -> None:
        self.queue.put(message)

    def shutdown(self) -> None:
        self._manager.shutdown()


def get_message_broker(name: str | None) -> InMemoryBroker:
    """Return a message broker instance by name."""

    if name in (None, "memory"):
        return InMemoryBroker()
    raise ValueError(f"Unsupported message broker: {name}")


class StorageCoordinator(multiprocessing.Process):
    """Background process that persists claims from a queue."""

    def __init__(self, queue: Queue, db_path: str) -> None:
        super().__init__(daemon=True)
        self._queue = queue
        self._db_path = db_path

    def run(self) -> None:  # pragma: no cover - runs in separate process
        storage.setup(self._db_path)
        while True:
            msg = self._queue.get()
            if msg.get("action") == "stop":
                break
            if msg.get("action") == "persist_claim":
                storage.StorageManager.persist_claim(
                    msg["claim"], msg.get("partial_update", False)
                )
        storage.teardown()


class ResultAggregator(multiprocessing.Process):
    """Collect results from agents running in other processes."""

    def __init__(self, queue: Queue) -> None:
        super().__init__(daemon=True)
        self._queue = queue
        self._manager = multiprocessing.Manager()
        self.results: list[dict[str, Any]] = self._manager.list()

    def run(self) -> None:  # pragma: no cover - runs in separate process
        while True:
            msg = self._queue.get()
            if msg.get("action") == "stop":
                break
            if msg.get("action") == "agent_result":
                self.results.append(msg)


def start_storage_coordinator(config: ConfigModel) -> tuple[StorageCoordinator, InMemoryBroker]:
    """Start a storage coordinator according to the distributed config."""

    broker = get_message_broker(getattr(config.distributed_config, "message_broker", None))
    db_path = config.storage.duckdb_path
    coordinator = StorageCoordinator(broker.queue, db_path)
    coordinator.start()
    return coordinator, broker


def publish_claim(broker: InMemoryBroker, claim: dict[str, Any], partial_update: bool = False) -> None:
    """Publish a claim persistence request to the broker."""

    broker.publish({"action": "persist_claim", "claim": claim, "partial_update": partial_update})


def start_result_aggregator(config: ConfigModel) -> tuple[ResultAggregator, InMemoryBroker]:
    """Start a background aggregator process for agent results."""

    broker = get_message_broker(getattr(config.distributed_config, "message_broker", None))
    aggregator = ResultAggregator(broker.queue)
    aggregator.start()
    return aggregator, broker


@ray.remote
def _execute_agent_remote(
    agent_name: str,
    state: QueryState,
    config: ConfigModel,
    queue: Queue | None = None,
) -> Dict[str, Any]:
    """Execute a single agent in a Ray worker."""
    agent = AgentFactory.get(agent_name)
    result = agent.execute(state, config)
    msg = {"action": "agent_result", "agent": agent_name, "result": result, "pid": os.getpid()}
    if queue is not None:
        queue.put(msg)
    return msg


class RayExecutor:
    """Simple distributed orchestrator that dispatches agents via Ray."""

    def __init__(self, config: ConfigModel) -> None:
        self.config = config
        address = None
        num_cpus = None
        if hasattr(config, "distributed_config"):
            cfg = config.distributed_config
            address = cfg.address
            num_cpus = cfg.num_cpus
        ray.init(address=address, num_cpus=num_cpus, ignore_reinit_error=True, configure_logging=False)

        self.storage_coordinator: Optional[StorageCoordinator] = None
        self.broker: Optional[InMemoryBroker] = None
        self.result_aggregator: Optional[ResultAggregator] = None
        self.result_broker: Optional[InMemoryBroker] = None
        if getattr(config, "distributed", False):
            self.storage_coordinator, self.broker = start_storage_coordinator(config)
            self.result_aggregator, self.result_broker = start_result_aggregator(config)

    def run_query(self, query: str, callbacks: Dict[str, Callable[..., None]] | None = None) -> QueryResponse:
        """Run agents in parallel across processes."""
        callbacks = callbacks or {}
        state = QueryState(query=query, primus_index=getattr(self.config, "primus_start", 0))
        for loop in range(self.config.loops):
            if self.result_aggregator:
                self.result_aggregator.results[:] = []
            futures = [
                _execute_agent_remote.remote(
                    name,
                    state,
                    self.config,
                    self.result_broker.queue if self.result_broker else None,
                )
                for name in self.config.agents
            ]
            remote_results = ray.get(futures)
            results = (
                list(self.result_aggregator.results) if self.result_aggregator else remote_results
            )
            if self.result_aggregator:
                self.result_aggregator.results[:] = []
            for res in results:
                state.update(res["result"])
            if callbacks.get("on_cycle_end"):
                callbacks["on_cycle_end"](loop, state)
            state.cycle += 1
        return state.synthesize()

    def shutdown(self) -> None:
        """Shut down Ray and any storage coordinator."""

        if self.broker and self.storage_coordinator:
            self.broker.publish({"action": "stop"})
            self.storage_coordinator.join()
            self.broker.shutdown()
        if self.result_broker and self.result_aggregator:
            self.result_broker.publish({"action": "stop"})
            self.result_aggregator.join()
            self.result_broker.shutdown()
        ray.shutdown()
