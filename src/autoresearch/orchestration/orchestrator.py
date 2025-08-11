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
from .budgeting import _apply_adaptive_token_budget
from .circuit_breaker import CircuitBreakerManager, CircuitBreakerState
from .execution import (
    _call_agent_start_callback,
    _check_agent_can_execute,
    _deliver_messages,
    _execute_agent,
    _execute_agent_with_token_counting,
    _execute_cycle,
    _execute_cycle_async,
    _get_agent,
    _handle_agent_completion,
    _log_agent_execution,
    _log_sources,
    _persist_claims,
    _rotate_list,
)
from .error_handling import (
    _apply_recovery_strategy,
    _categorize_error,
    _handle_agent_error,
)
from .metrics import OrchestrationMetrics, record_query
from .reasoning import ChainOfThoughtStrategy, ReasoningMode
from .state import QueryState
from .token_utils import _capture_token_usage as capture_token_usage
from .token_utils import _execute_with_adapter as execute_with_adapter
from .utils import calculate_result_confidence, get_memory_usage

log = get_logger(__name__)


class Orchestrator:
    """Coordinates multi-agent dialectical cycles with rotating Primus."""

    _cb_manager: CircuitBreakerManager | None = None

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

    @staticmethod
    def get_circuit_breaker_state(agent_name: str) -> CircuitBreakerState:
        if Orchestrator._cb_manager is None:
            return {
                "state": "closed",
                "failure_count": 0.0,
                "last_failure_time": 0.0,
                "recovery_attempts": 0,
            }
        return Orchestrator._cb_manager.get_circuit_breaker_state(agent_name)

    @staticmethod
    def run_query(
        query: str,
        config: ConfigModel,
        callbacks: Dict[str, Callable[..., None]] | None = None,
        *,
        agent_factory: type[AgentFactory] = AgentFactory,
        storage_manager: type[StorageManager] = StorageManager,
    ) -> QueryResponse:
        """Run a query through dialectical agent cycles."""
        setup_tracing(getattr(config, "tracing_enabled", False))
        tracer = get_tracer(__name__)
        record_query()
        metrics = OrchestrationMetrics()
        callbacks = callbacks or {}

        config_params = Orchestrator._parse_config(config)
        agents = config_params["agent_groups"]
        primus_index = config_params["primus_index"]
        loops = config_params["loops"]
        mode = config_params["mode"]
        max_errors = config_params["max_errors"]
        cb_manager = CircuitBreakerManager(
            config_params["circuit_breaker_threshold"],
            config_params["circuit_breaker_cooldown"],
        )
        Orchestrator._cb_manager = cb_manager

        Orchestrator._apply_adaptive_token_budget(config, query)  # type: ignore[attr-defined]

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

            primus_index = Orchestrator._execute_cycle(  # type: ignore[attr-defined]
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

    @staticmethod
    async def run_query_async(
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

        config_params = Orchestrator._parse_config(config)
        agents = config_params["agent_groups"]
        primus_index = config_params["primus_index"]
        loops = config_params["loops"]
        mode = config_params["mode"]
        max_errors = config_params["max_errors"]
        cb_manager = CircuitBreakerManager(
            config_params["circuit_breaker_threshold"],
            config_params["circuit_breaker_cooldown"],
        )
        Orchestrator._cb_manager = cb_manager

        Orchestrator._apply_adaptive_token_budget(config, query)  # type: ignore[attr-defined]

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

            primus_index = await Orchestrator._execute_cycle_async(  # type: ignore[attr-defined]
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


# Attach helper functions from submodules
Orchestrator._get_agent = staticmethod(_get_agent)  # type: ignore[attr-defined]
Orchestrator._check_agent_can_execute = staticmethod(  # type: ignore[attr-defined]
    _check_agent_can_execute
)
Orchestrator._deliver_messages = staticmethod(_deliver_messages)  # type: ignore[attr-defined]
Orchestrator._log_agent_execution = staticmethod(  # type: ignore[attr-defined]
    _log_agent_execution
)
Orchestrator._call_agent_start_callback = staticmethod(  # type: ignore[attr-defined]
    _call_agent_start_callback
)
Orchestrator._execute_agent_with_token_counting = staticmethod(  # type: ignore[attr-defined]
    _execute_agent_with_token_counting
)
Orchestrator._handle_agent_completion = staticmethod(  # type: ignore[attr-defined]
    _handle_agent_completion
)
Orchestrator._log_sources = staticmethod(_log_sources)  # type: ignore[attr-defined]
Orchestrator._persist_claims = staticmethod(_persist_claims)  # type: ignore[attr-defined]
Orchestrator._handle_agent_error = staticmethod(_handle_agent_error)  # type: ignore[attr-defined]
Orchestrator._categorize_error = staticmethod(_categorize_error)  # type: ignore[attr-defined]
Orchestrator._apply_recovery_strategy = staticmethod(  # type: ignore[attr-defined]
    _apply_recovery_strategy
)
Orchestrator._execute_agent = staticmethod(_execute_agent)  # type: ignore[attr-defined]
Orchestrator._execute_cycle = staticmethod(_execute_cycle)  # type: ignore[attr-defined]
Orchestrator._execute_cycle_async = staticmethod(  # type: ignore[attr-defined]
    _execute_cycle_async
)
Orchestrator._rotate_list = staticmethod(_rotate_list)  # type: ignore[attr-defined]
Orchestrator._apply_adaptive_token_budget = staticmethod(  # type: ignore[attr-defined]
    _apply_adaptive_token_budget
)
Orchestrator._get_memory_usage = staticmethod(get_memory_usage)  # type: ignore[attr-defined]
Orchestrator._calculate_result_confidence = staticmethod(  # type: ignore[attr-defined]
    calculate_result_confidence
)
Orchestrator._capture_token_usage = staticmethod(capture_token_usage)  # type: ignore[attr-defined]
Orchestrator._execute_with_adapter = staticmethod(  # type: ignore[attr-defined]
    execute_with_adapter
)
