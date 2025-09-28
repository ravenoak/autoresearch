"""Utilities for distributed agent execution using Ray or multiprocessing."""

from __future__ import annotations

import multiprocessing
import os
from typing import Any, Optional, cast

from .. import search, storage
from ..agents.registry import AgentFactory
from ..config.models import ConfigModel
from ..interfaces import CallbackMap, QueryStateLike
from ..llm import pool as llm_pool
from ..logging_utils import get_logger
from ..models import QueryResponse
from ..orchestration.state import QueryState
from ._ray import RayLike, RayObjectRef, RemoteFunction, optional_ray
from .broker import (
    AgentResultMessage,
    BrokerType,
    MessageQueueProtocol,
    STOP_MESSAGE,
)
from .coordinator import (
    ResultAggregator,
    StorageCoordinator,
    publish_claim,
    start_result_aggregator,
    start_storage_coordinator,
)

ray: RayLike = optional_ray()

log = get_logger(__name__)


@ray.remote
def _execute_agent_remote(
    agent_name: str,
    state: QueryStateLike,
    config: ConfigModel,
    result_queue: MessageQueueProtocol | None = None,
    storage_queue: MessageQueueProtocol | None = None,
    http_session: Any | None = None,
    llm_session: Any | None = None,
) -> AgentResultMessage:
    """Execute a single agent in a Ray worker."""
    if storage_queue is not None:
        storage.set_message_queue(storage_queue)
    if http_session is not None:
        try:
            if isinstance(http_session, ray.ObjectRef):
                http_session = ray.get(http_session)
        except Exception as e:
            log.warning("Failed to retrieve HTTP session", exc_info=e)
        from .. import search

        search.set_http_session(http_session)
    if llm_session is not None:
        try:
            if isinstance(llm_session, ray.ObjectRef):
                llm_session = ray.get(llm_session)
        except Exception as e:
            log.warning("Failed to retrieve LLM session", exc_info=e)
        from ..llm import pool as llm_pool

        llm_pool.set_session(llm_session)
    agent = AgentFactory.get(agent_name)
    result = agent.execute(cast(QueryState, state), config)
    msg: AgentResultMessage = {
        "action": "agent_result",
        "agent": agent_name,
        "result": result,
        "pid": os.getpid(),
    }
    if result_queue is not None:
        result_queue.put(msg)
    return msg


def _execute_agent_process(
    agent_name: str,
    state: QueryStateLike,
    config: ConfigModel,
    result_queue: MessageQueueProtocol | None = None,
    storage_queue: MessageQueueProtocol | None = None,
) -> AgentResultMessage:
    """Execute a single agent in a spawned process."""
    if storage_queue is not None:
        storage.set_message_queue(storage_queue)
    agent = AgentFactory.get(agent_name)
    result = agent.execute(cast(QueryState, state), config)
    msg: AgentResultMessage = {
        "action": "agent_result",
        "agent": agent_name,
        "result": result,
        "pid": os.getpid(),
    }
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
        ray.init(
            address=address, num_cpus=num_cpus, ignore_reinit_error=True, configure_logging=False
        )

        self.storage_coordinator: Optional[StorageCoordinator] = None
        self.broker: Optional[BrokerType] = None
        self.result_aggregator: Optional[ResultAggregator] = None
        self.result_broker: Optional[BrokerType] = None
        self.http_session = search.get_http_session()
        self.llm_session = llm_pool.get_session()
        self.http_handle: RayObjectRef[Any] = ray.put(self.http_session)
        self.llm_handle: RayObjectRef[Any] = ray.put(self.llm_session)
        should_start = getattr(config, "distributed", False) or config.distributed_config.enabled
        if should_start:
            self.storage_coordinator, self.broker = start_storage_coordinator(config)
            storage.set_message_queue(self.broker.queue)
            self.result_aggregator, self.result_broker = start_result_aggregator(config)

    def run_query(self, query: str, callbacks: CallbackMap | None = None) -> QueryResponse:
        """Run agents in parallel across processes."""
        callbacks = callbacks or {}
        state = QueryState(query=query, primus_index=getattr(self.config, "primus_start", 0))
        for loop in range(self.config.loops):
            if self.result_aggregator:
                self.result_aggregator.results[:] = []
        remote_executor: RemoteFunction[AgentResultMessage] = _execute_agent_remote
        futures: list[RayObjectRef[AgentResultMessage]] = [
            remote_executor.remote(
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
        remote_results = cast(list[AgentResultMessage], ray.get(futures))
        results: list[AgentResultMessage]
        if self.result_aggregator:
            results = list(self.result_aggregator.results)
            self.result_aggregator.results[:] = []
        else:
            results = remote_results

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
            try:
                self.broker.publish(STOP_MESSAGE)
            except Exception as e:
                log.warning("Failed to publish stop message", exc_info=e)
            self.storage_coordinator.join()
            try:
                self.broker.shutdown()
            except Exception as e:
                log.warning("Failed to shutdown broker", exc_info=e)
            storage.set_message_queue(None)
        if self.result_broker and self.result_aggregator:
            try:
                self.result_broker.publish(STOP_MESSAGE)
            except Exception as e:
                log.warning("Failed to publish stop to result broker", exc_info=e)
            self.result_aggregator.join()
            try:
                self.result_broker.shutdown()
            except Exception as e:
                log.warning("Failed to shutdown result broker", exc_info=e)
        if hasattr(ray, "shutdown"):
            ray.shutdown()


class ProcessExecutor:
    """Distributed orchestrator using Python multiprocessing."""

    def __init__(self, config: ConfigModel) -> None:
        self.config = config
        self.storage_coordinator: Optional[StorageCoordinator] = None
        self.broker: Optional[BrokerType] = None
        self.result_aggregator: Optional[ResultAggregator] = None
        self.result_broker: Optional[BrokerType] = None
        should_start = getattr(config, "distributed", False) or config.distributed_config.enabled
        if should_start:
            self.storage_coordinator, self.broker = start_storage_coordinator(config)
            storage.set_message_queue(self.broker.queue)
            self.result_aggregator, self.result_broker = start_result_aggregator(config)

    def run_query(self, query: str, callbacks: CallbackMap | None = None) -> QueryResponse:
        callbacks = callbacks or {}
        state = QueryState(query=query, primus_index=getattr(self.config, "primus_start", 0))
        ctx = multiprocessing.get_context("spawn")
        for loop in range(self.config.loops):
            if self.result_aggregator:
                self.result_aggregator.results[:] = []
            with ctx.Pool(processes=self.config.distributed_config.num_cpus) as pool:
                results: list[AgentResultMessage] = pool.starmap(
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
            aggregated: list[AgentResultMessage]
            if self.result_aggregator:
                aggregated = list(self.result_aggregator.results)
            else:
                aggregated = results
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
            try:
                self.broker.publish(STOP_MESSAGE)
            except Exception as e:
                log.warning("Failed to publish stop message", exc_info=e)
            self.storage_coordinator.join()
            try:
                self.broker.shutdown()
            except Exception as e:
                log.warning("Failed to shutdown broker", exc_info=e)
            storage.set_message_queue(None)
        if self.result_broker and self.result_aggregator:
            try:
                self.result_broker.publish(STOP_MESSAGE)
            except Exception as e:
                log.warning("Failed to publish stop to result broker", exc_info=e)
            self.result_aggregator.join()
            try:
                self.result_broker.shutdown()
            except Exception as e:
                log.warning("Failed to shutdown result broker", exc_info=e)
