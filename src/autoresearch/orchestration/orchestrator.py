"""
Orchestration system coordinating multi-agent dialectical cycles.

Provides direct, dialectical, and chain-of-thought reasoning modes with
state management, metrics, token tracking, and parallel execution. Behavior
is exercised by unit and integration tests under ``tests/``.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List

import rdflib

from ..agents.registry import AgentFactory, AgentRegistry
from ..config.models import ConfigModel
from ..errors import (  # noqa: F401
    AgentError,
    NotFoundError,
    OrchestrationError,
    TimeoutError,
)
from ..logging_utils import get_logger
from ..models import QueryResponse
from ..storage import StorageManager
from ..tracing import get_tracer, setup_tracing
from .circuit_breaker import CircuitBreakerManager, CircuitBreakerState
from .metrics import OrchestrationMetrics, record_query
from .orchestration_utils import OrchestrationUtils
from .reasoning import ChainOfThoughtStrategy, ReasoningMode
from .state import QueryState
from .token_utils import _capture_token_usage

log = get_logger(__name__)


class Orchestrator:
    """Coordinates multi-agent dialectical cycles with rotating Primus."""

    # Expose token usage capture helper for tests that monkeypatch the
    # orchestrator directly. Previously this utility lived only within
    # ``token_utils``, which caused AttributeError in tests expecting
    # ``Orchestrator._capture_token_usage``.
    _capture_token_usage = staticmethod(_capture_token_usage)

    def __init__(self) -> None:
        """Initialize orchestrator state for a single query."""
        self._cb_manager: CircuitBreakerManager | None = None

    @staticmethod
    def _parse_config(config: ConfigModel) -> Dict[str, Any]:
        """Parse configuration and extract relevant parameters."""
        agents = getattr(
            config,
            "agents",
            ["Synthesizer", "Contrarian", "FactChecker"],
        )
        primus_index = 0 if not hasattr(config, "primus_start") else config.primus_start
        loops = config.loops if hasattr(config, "loops") else 2
        mode = getattr(config, "reasoning_mode", ReasoningMode.DIALECTICAL)
        max_errors = config.max_errors if hasattr(config, "max_errors") else 3
        cb_threshold = getattr(config, "circuit_breaker_threshold", 3)
        cb_cooldown = getattr(config, "circuit_breaker_cooldown", 30)
        retry_attempts = getattr(config, "retry_attempts", 1)
        retry_backoff = getattr(config, "retry_backoff", 0.0)
        enable_messages = getattr(config, "enable_agent_messages", False)
        coalitions = getattr(config, "coalitions", {})
        for cname, members in coalitions.items():
            AgentRegistry.create_coalition(cname, members)
        enable_feedback = getattr(config, "enable_feedback", False)

        agent_groups: List[List[str]] = []
        if mode == ReasoningMode.DIRECT:
            agents = ["Synthesizer"]
            loops = 1
            agent_groups = [["Synthesizer"]]
        else:
            for a in agents:
                coalition = AgentRegistry.get_coalition_obj(a)
                if coalition:
                    agent_groups.append(coalition.members)
                else:
                    agent_groups.append([a])

        return {
            "agents": agents,
            "agent_groups": agent_groups,
            "primus_index": primus_index,
            "loops": loops,
            "mode": mode,
            "max_errors": max_errors,
            "circuit_breaker_threshold": cb_threshold,
            "circuit_breaker_cooldown": cb_cooldown,
            "retry_attempts": retry_attempts,
            "retry_backoff": retry_backoff,
            "enable_agent_messages": enable_messages,
            "enable_feedback": enable_feedback,
            "coalitions": coalitions,
        }

    def get_circuit_breaker_state(self, agent_name: str) -> CircuitBreakerState:
        if self._cb_manager is None:
            return {
                "state": "closed",
                "failure_count": 0.0,
                "last_failure_time": 0.0,
                "recovery_attempts": 0,
            }
        return self._cb_manager.get_circuit_breaker_state(agent_name)

    def run_query(
        self,
        query: str,
        config: ConfigModel,
        callbacks: Dict[str, Callable[..., None]] | None = None,
        *,
        agent_factory: type[AgentFactory] = AgentFactory,
        storage_manager: type[StorageManager] = StorageManager,
        visualize: bool = False,
    ) -> QueryResponse:
        """Run a query through dialectical agent cycles."""
        setup_tracing(getattr(config, "tracing_enabled", False))
        tracer = get_tracer(__name__)
        record_query()
        metrics = OrchestrationMetrics()
        callbacks = callbacks or {}

        if visualize:
            log.debug("Visualization requested for query")

        config_params = self._parse_config(config)
        agents = config_params["agent_groups"]
        primus_index = config_params["primus_index"]
        loops = config_params["loops"]
        mode = config_params["mode"]
        max_errors = config_params["max_errors"]
        cb_manager = CircuitBreakerManager(
            config_params["circuit_breaker_threshold"],
            config_params["circuit_breaker_cooldown"],
        )
        self._cb_manager = cb_manager

        OrchestrationUtils.apply_adaptive_token_budget(config, query)

        token_budget = getattr(config, "token_budget", None)
        if (
            token_budget is not None
            and hasattr(config, "group_size")
            and hasattr(config, "total_groups")
        ):
            total_agents = getattr(
                config,
                "total_agents",
                config.group_size * config.total_groups,
            )
            if total_agents:
                group_tokens = max(1, token_budget * config.group_size // total_agents)
                config.token_budget = group_tokens

        if mode == ReasoningMode.CHAIN_OF_THOUGHT:
            strategy = ChainOfThoughtStrategy()
            return strategy.run_query(
                query,
                config,
                agent_factory=agent_factory,
            )

        state = QueryState(
            query=query,
            primus_index=primus_index,
            coalitions=config_params.get("coalitions", {}),
        )

        total_agents = sum(len(g) for g in agents)
        log.info(
            f"Starting dialectical process with {total_agents} agents in {len(agents)} groups and {loops} loops",
            extra={
                "agents": agents,
                "loops": loops,
                "primus_index": primus_index,
                "max_errors": max_errors,
                "reasoning_mode": str(mode),
            },
        )

        for loop in range(loops):
            log.debug(
                f"Starting loop {loop + 1}/{loops} with primus_index {primus_index}",
                extra={
                    "loop": loop + 1,
                    "total_loops": loops,
                    "primus_index": primus_index,
                },
            )

            primus_index = OrchestrationUtils.execute_cycle(
                loop,
                loops,
                agents,
                primus_index,
                max_errors,
                state,
                config,
                metrics,
                callbacks,
                agent_factory,
                storage_manager,
                tracer,
                cb_manager,
            )

            if "error" in state.results:
                log.error(
                    f"Aborting dialectical process due to error: {state.results['error']}",
                    extra={
                        "error": state.results["error"],
                        "error_count": state.error_count,
                    },
                )
                break

            log.debug(
                f"Completed loop {loop + 1}/{loops}, new primus_index: {primus_index}",
                extra={
                    "loop": loop + 1,
                    "total_loops": loops,
                    "primus_index": primus_index,
                    "cycle": state.cycle,
                    "error_count": state.error_count,
                },
            )

        state.metadata["execution_metrics"] = metrics.get_summary()
        metrics.record_query_tokens(query)

        if "error" in state.results or state.error_count > 0:
            error_message = state.results.get(
                "error", f"Process completed with {state.error_count} errors"
            )
            raise OrchestrationError(
                error_message,
                cause=None,
                errors=state.metadata.get("errors", []),
                suggestion="Check the agent execution logs for details on the specific error and ensure all agents are properly configured",
            )

        return state.synthesize()

    async def run_query_async(
        self,
        query: str,
        config: ConfigModel,
        callbacks: Dict[str, Callable[..., None]] | None = None,
        *,
        agent_factory: type[AgentFactory] = AgentFactory,
        storage_manager: type[StorageManager] = StorageManager,
        concurrent: bool = False,
    ) -> QueryResponse:
        """Asynchronous wrapper around :meth:`run_query`."""
        setup_tracing(getattr(config, "tracing_enabled", False))
        tracer = get_tracer(__name__)
        record_query()
        metrics = OrchestrationMetrics()
        callbacks = callbacks or {}

        config_params = self._parse_config(config)
        agents = config_params["agent_groups"]
        primus_index = config_params["primus_index"]
        loops = config_params["loops"]
        mode = config_params["mode"]
        max_errors = config_params["max_errors"]
        cb_manager = CircuitBreakerManager(
            config_params["circuit_breaker_threshold"],
            config_params["circuit_breaker_cooldown"],
        )
        self._cb_manager = cb_manager

        OrchestrationUtils.apply_adaptive_token_budget(config, query)

        token_budget = getattr(config, "token_budget", None)
        if (
            token_budget is not None
            and hasattr(config, "group_size")
            and hasattr(config, "total_groups")
        ):
            total_agents = getattr(
                config,
                "total_agents",
                config.group_size * config.total_groups,
            )
            if total_agents:
                group_tokens = max(1, token_budget * config.group_size // total_agents)
                config.token_budget = group_tokens

        if mode == ReasoningMode.CHAIN_OF_THOUGHT:
            strategy = ChainOfThoughtStrategy()
            return await asyncio.to_thread(
                strategy.run_query,
                query,
                config,
                agent_factory=agent_factory,
            )

        state = QueryState(
            query=query,
            primus_index=primus_index,
            coalitions=config_params.get("coalitions", {}),
        )

        total_agents = sum(len(g) for g in agents)
        log.info(
            f"Starting dialectical process with {total_agents} agents in {len(agents)} groups and {loops} loops",
            extra={
                "agents": agents,
                "loops": loops,
                "primus_index": primus_index,
                "max_errors": max_errors,
                "reasoning_mode": str(mode),
            },
        )

        for loop in range(loops):
            log.debug(
                f"Starting loop {loop + 1}/{loops} with primus_index {primus_index}",
                extra={
                    "loop": loop + 1,
                    "total_loops": loops,
                    "primus_index": primus_index,
                },
            )

            primus_index = await OrchestrationUtils.execute_cycle_async(
                loop,
                loops,
                agents,
                primus_index,
                max_errors,
                state,
                config,
                metrics,
                callbacks,
                agent_factory,
                storage_manager,
                tracer,
                concurrent=concurrent,
                cb_manager=cb_manager,
            )

            if "error" in state.results:
                log.error(
                    f"Aborting dialectical process due to error: {state.results['error']}",
                    extra={
                        "error": state.results["error"],
                        "error_count": state.error_count,
                    },
                )
                break

            log.debug(
                f"Completed loop {loop + 1}/{loops}, new primus_index: {primus_index}",
                extra={
                    "loop": loop + 1,
                    "total_loops": loops,
                    "primus_index": primus_index,
                    "cycle": state.cycle,
                    "error_count": state.error_count,
                },
            )

        state.metadata["execution_metrics"] = metrics.get_summary()
        metrics.record_query_tokens(query)

        if "error" in state.results or state.error_count > 0:
            error_message = state.results.get(
                "error", f"Process completed with {state.error_count} errors"
            )
            raise OrchestrationError(
                error_message,
                cause=None,
                errors=state.metadata.get("errors", []),
                suggestion="Check the agent execution logs for details on the specific error and ensure all agents are properly configured",
            )

        return state.synthesize()

    @staticmethod
    def run_parallel_query(
        query: str,
        config: ConfigModel,
        agent_groups: List[List[str]],
        timeout: int = 300,
    ) -> QueryResponse:
        """Run multiple parallel agent groups and synthesize results."""
        from . import parallel

        return parallel.execute_parallel_query(query, config, agent_groups, timeout)

    @staticmethod
    def infer_relations() -> None:
        """Infer ontology relations via the storage manager."""
        StorageManager.infer_relations()

    @staticmethod
    def query_ontology(query: str) -> rdflib.query.Result:
        """Query the ontology graph via the storage manager."""
        return StorageManager.query_ontology(query)
