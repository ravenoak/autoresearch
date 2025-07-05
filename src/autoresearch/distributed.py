"""Utilities for distributed agent execution using Ray or multiprocessing."""

from __future__ import annotations

from typing import Dict, Callable, Any, Optional, TYPE_CHECKING
import os
import json
import multiprocessing

from queue import Queue

from . import storage, search
from .llm import pool as llm_pool

import ray

from .config import ConfigModel

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    import redis
from .orchestration.state import QueryState
from .orchestration.orchestrator import AgentFactory
from .models import QueryResponse


class InMemoryBroker:
    """Simple in-memory message broker using multiprocessing.Queue."""

    def __init__(self) -> None:
        self._manager = multiprocessing.Manager()
        self.queue: Queue[Any] = self._manager.Queue()

    def publish(self, message: dict[str, Any]) -> None:
        self.queue.put(message)

    def shutdown(self) -> None:
        self._manager.shutdown()


class RedisQueue:
    """Minimal queue wrapper backed by Redis lists."""

    def __init__(self, client: "redis.Redis", name: str) -> None:
        self.client = client
        self.name = name

    def put(self, message: dict[str, Any]) -> None:
        self.client.rpush(self.name, json.dumps(message))

    def get(self) -> dict[str, Any]:
        _, data = self.client.blpop(self.name)
        return json.loads(data)


class RedisBroker:
    """Message broker backed by Redis."""

    def __init__(self, url: str | None = None, queue_name: str = "autoresearch") -> None:
        import redis

        self.client = redis.Redis.from_url(url or "redis://localhost:6379/0")
        self.queue = RedisQueue(self.client, queue_name)

    def publish(self, message: dict[str, Any]) -> None:
        self.queue.put(message)

    def shutdown(self) -> None:
        self.client.close()


BrokerType = InMemoryBroker | RedisBroker


def get_message_broker(name: str | None, url: str | None = None) -> BrokerType:
    """Return a message broker instance by name."""

    if name in (None, "memory"):
        return InMemoryBroker()
    if name == "redis":
        return RedisBroker(url)
    raise ValueError(f"Unsupported message broker: {name}")


class StorageCoordinator(multiprocessing.Process):
    """Background process that persists claims from a queue."""

    def __init__(self, queue: Any, db_path: str) -> None:
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

    def __init__(self, queue: Any) -> None:
        super().__init__(daemon=True)
        self._queue = queue
        self._manager = multiprocessing.Manager()
        self.results: multiprocessing.managers.ListProxy[dict[str, Any]] = self._manager.list()  # type: ignore[attr-defined]

    def run(self) -> None:  # pragma: no cover - runs in separate process
        while True:
            msg = self._queue.get()
            if msg.get("action") == "stop":
                break
            if msg.get("action") == "agent_result":
                self.results.append(msg)


def start_storage_coordinator(config: ConfigModel) -> tuple[StorageCoordinator, BrokerType]:
    """Start a storage coordinator according to the distributed config."""

    dist_cfg = config.distributed_config
    broker = get_message_broker(getattr(dist_cfg, "message_broker", None), getattr(dist_cfg, "broker_url", None))
    db_path = config.storage.duckdb_path
    coordinator = StorageCoordinator(broker.queue, db_path)
    coordinator.start()
    return coordinator, broker


def publish_claim(broker: BrokerType, claim: dict[str, Any], partial_update: bool = False) -> None:
    """Publish a claim persistence request to the broker."""

    broker.publish({"action": "persist_claim", "claim": claim, "partial_update": partial_update})


def start_result_aggregator(config: ConfigModel) -> tuple[ResultAggregator, BrokerType]:
    """Start a background aggregator process for agent results."""

    dist_cfg = config.distributed_config
    broker = get_message_broker(getattr(dist_cfg, "message_broker", None), getattr(dist_cfg, "broker_url", None))
    aggregator = ResultAggregator(broker.queue)
    aggregator.start()
    return aggregator, broker


@ray.remote
def _execute_agent_remote(
    agent_name: str,
    state: QueryState,
    config: ConfigModel,
    result_queue: Queue | None = None,
    storage_queue: Queue | None = None,
    http_session: Any | None = None,
    llm_session: Any | None = None,
) -> Dict[str, Any]:
    """Execute a single agent in a Ray worker."""
    if storage_queue is not None:
        storage.set_message_queue(storage_queue)
    if http_session is not None:
        try:
            import ray
            if isinstance(http_session, ray.ObjectRef):
                http_session = ray.get(http_session)
        except Exception:
            pass
        from . import search
        search.set_http_session(http_session)
    if llm_session is not None:
        try:
            import ray
            if isinstance(llm_session, ray.ObjectRef):
                llm_session = ray.get(llm_session)
        except Exception:
            pass
        from .llm import pool as llm_pool
        llm_pool.set_session(llm_session)
    agent = AgentFactory.get(agent_name)
    result = agent.execute(state, config)
    msg = {"action": "agent_result", "agent": agent_name, "result": result, "pid": os.getpid()}
    if result_queue is not None:
        result_queue.put(msg)
    return msg


def _execute_agent_process(
    agent_name: str,
    state: QueryState,
    config: ConfigModel,
    result_queue: Queue | None = None,
    storage_queue: Queue | None = None,
) -> Dict[str, Any]:
    """Execute a single agent in a spawned process."""
    if storage_queue is not None:
        storage.set_message_queue(storage_queue)
    agent = AgentFactory.get(agent_name)
    result = agent.execute(state, config)
    msg = {"action": "agent_result", "agent": agent_name, "result": result, "pid": os.getpid()}
    if result_queue is not None:
        result_queue.put(msg)
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
        self.broker: Optional[BrokerType] = None
        self.result_aggregator: Optional[ResultAggregator] = None
        self.result_broker: Optional[BrokerType] = None
        self.http_session = search.get_http_session()
        self.llm_session = llm_pool.get_session()
        self.http_handle = ray.put(self.http_session)
        self.llm_handle = ray.put(self.llm_session)
        if getattr(config, "distributed", False):
            self.storage_coordinator, self.broker = start_storage_coordinator(config)
            storage.set_message_queue(self.broker.queue)
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
                    self.broker.queue if self.broker else None,
                    self.http_handle,
                    self.llm_handle,
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
                if self.broker:
                    for claim in res["result"].get("claims", []):
                        publish_claim(self.broker, claim)
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
            storage.set_message_queue(None)
        if self.result_broker and self.result_aggregator:
            self.result_broker.publish({"action": "stop"})
            self.result_aggregator.join()
            self.result_broker.shutdown()
        ray.shutdown()


class ProcessExecutor:
    """Distributed orchestrator using Python multiprocessing."""

    def __init__(self, config: ConfigModel) -> None:
        self.config = config
        self.storage_coordinator: Optional[StorageCoordinator] = None
        self.broker: Optional[BrokerType] = None
        self.result_aggregator: Optional[ResultAggregator] = None
        self.result_broker: Optional[BrokerType] = None
        if getattr(config, "distributed", False):
            self.storage_coordinator, self.broker = start_storage_coordinator(config)
            storage.set_message_queue(self.broker.queue)
            self.result_aggregator, self.result_broker = start_result_aggregator(config)

    def run_query(self, query: str, callbacks: Dict[str, Callable[..., None]] | None = None) -> QueryResponse:
        callbacks = callbacks or {}
        state = QueryState(query=query, primus_index=getattr(self.config, "primus_start", 0))
        ctx = multiprocessing.get_context("spawn")
        for loop in range(self.config.loops):
            if self.result_aggregator:
                self.result_aggregator.results[:] = []
            with ctx.Pool(processes=self.config.distributed_config.num_cpus) as pool:
                results = pool.starmap(
                    _execute_agent_process,
                    [
                        (
                            name,
                            state,
                            self.config,
                            self.result_broker.queue if self.result_broker else None,
                            self.broker.queue if self.broker else None,
                        )
                        for name in self.config.agents
                    ],
                )
            aggregated = list(self.result_aggregator.results) if self.result_aggregator else results
            if self.result_aggregator:
                self.result_aggregator.results[:] = []
            for res in aggregated:
                state.update(res["result"])
                if self.broker:
                    for claim in res["result"].get("claims", []):
                        publish_claim(self.broker, claim)
            if callbacks.get("on_cycle_end"):
                callbacks["on_cycle_end"](loop, state)
            state.cycle += 1
        return state.synthesize()

    def shutdown(self) -> None:
        if self.broker and self.storage_coordinator:
            self.broker.publish({"action": "stop"})
            self.storage_coordinator.join()
            self.broker.shutdown()
            storage.set_message_queue(None)
        if self.result_broker and self.result_aggregator:
            self.result_broker.publish({"action": "stop"})
            self.result_aggregator.join()
            self.result_broker.shutdown()
