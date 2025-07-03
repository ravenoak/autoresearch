"""
Orchestration system for coordinating multi-agent dialectical cycles.

This module provides the core orchestration functionality for the Autoresearch system,
coordinating the execution of multiple agents in a dialectical reasoning process.
The orchestration system supports different reasoning modes:

1. Direct: Uses only a single agent (typically the Synthesizer)
2. Dialectical: Rotates through multiple agents in a thesis→antithesis→synthesis cycle
3. Chain-of-thought: Loops a single agent (typically the Synthesizer) multiple times

The Orchestrator class handles:
- Executing agents in the correct order based on the reasoning mode
- Managing state between agent executions
- Collecting and reporting metrics
- Error handling and recovery
- Token usage tracking
- Parallel execution of agent groups

The system is designed to be extensible, allowing for custom agents, reasoning modes,
and execution strategies.
"""

from typing import List, Dict, Any, Callable, Iterator, TypedDict
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import asyncio

from ..agents.registry import AgentFactory
from ..config import ConfigModel
from .reasoning import ReasoningMode, ChainOfThoughtStrategy
from ..models import QueryResponse
from ..storage import StorageManager
from .state import QueryState
from .metrics import OrchestrationMetrics, record_query
from ..logging_utils import get_logger
from ..tracing import setup_tracing, get_tracer
from ..errors import OrchestrationError, AgentError, NotFoundError, TimeoutError


log = get_logger(__name__)


class CircuitBreakerState(TypedDict):
    """State information for an agent's circuit breaker."""

    failure_count: float
    last_failure_time: float
    state: str
    recovery_attempts: int


class Orchestrator:
    """Coordinates multi-agent dialectical cycles with rotating Primus."""

    @staticmethod
    def _parse_config(config: ConfigModel) -> Dict[str, Any]:
        """Parse configuration and extract relevant parameters.

        Args:
            config: System configuration

        Returns:
            Dictionary with parsed configuration parameters
        """
        # Get enabled agents and reasoning mode from config
        agents = getattr(
            config,
            "agents",
            ["Synthesizer", "Contrarian", "FactChecker"],
        )
        primus_index = 0 if not hasattr(config, "primus_start") else config.primus_start
        loops = config.loops if hasattr(config, "loops") else 2
        mode = getattr(config, "reasoning_mode", ReasoningMode.DIALECTICAL)
        max_errors = config.max_errors if hasattr(config, "max_errors") else 3

        # Adjust parameters based on reasoning mode
        if mode == ReasoningMode.DIRECT:
            agents = ["Synthesizer"]
            loops = 1

        return {
            "agents": agents,
            "primus_index": primus_index,
            "loops": loops,
            "mode": mode,
            "max_errors": max_errors,
        }

    @staticmethod
    def _get_agent(agent_name: str, agent_factory: type[AgentFactory]) -> Any:
        """Get an agent instance from the factory.

        Args:
            agent_name: Name of the agent to get
            agent_factory: Factory for creating agent instances

        Returns:
            The agent instance

        Raises:
            NotFoundError: If agent cannot be found
        """
        try:
            return agent_factory.get(agent_name)
        except Exception as e:
            # Wrap agent factory errors in NotFoundError
            raise NotFoundError(
                f"Agent '{agent_name}' not found",
                resource_type="agent",
                resource_id=agent_name,
                cause=e,
            )

    @staticmethod
    def _check_agent_can_execute(
        agent: Any, agent_name: str, state: QueryState, config: ConfigModel
    ) -> bool:
        """Check if an agent can execute.

        Args:
            agent: The agent to check
            agent_name: Name of the agent
            state: Current query state
            config: System configuration

        Returns:
            True if the agent can execute, False otherwise
        """
        if not agent.can_execute(state, config):
            log.info(f"Agent {agent_name} skipped execution (can_execute=False)")
            return False
        return True

    @staticmethod
    def _log_agent_execution(agent_name: str, state: QueryState, loop: int) -> None:
        """Log agent execution start.

        Args:
            agent_name: Name of the agent
            state: Current query state
            loop: Current loop number
        """
        log.info(
            f"Executing agent: {agent_name} (loop {loop + 1}, cycle {state.cycle})",
            extra={
                "agent": agent_name,
                "loop": loop + 1,
                "cycle": state.cycle,
                "query": state.query[:100] + "..."
                if len(state.query) > 100
                else state.query,
            },
        )

    @staticmethod
    def _call_agent_start_callback(
        agent_name: str, state: QueryState, callbacks: Dict[str, Callable[..., None]]
    ) -> None:
        """Call the on_agent_start callback if it exists.

        Args:
            agent_name: Name of the agent
            state: Current query state
            callbacks: Callbacks for monitoring execution
        """
        if callbacks.get("on_agent_start"):
            log.debug(f"Calling on_agent_start callback for {agent_name}")
            callbacks["on_agent_start"](agent_name, state)

    @staticmethod
    def _execute_agent_with_token_counting(
        agent: Any,
        agent_name: str,
        state: QueryState,
        config: ConfigModel,
        metrics: OrchestrationMetrics,
    ) -> Dict[str, Any]:
        """Execute an agent with token counting.

        Args:
            agent: The agent to execute
            agent_name: Name of the agent
            state: Current query state
            config: System configuration
            metrics: Metrics collector

        Returns:
            The result of agent execution

        Raises:
            TimeoutError: If agent execution times out
            AgentError: If agent execution fails
        """
        try:
            log.debug(f"Starting token counting for {agent_name}")
            with Orchestrator._capture_token_usage(agent_name, metrics, config) as (
                token_counter,
                wrapped_adapter,
            ):
                log.debug(
                    f"Executing {agent_name}.execute() with token counting adapter"
                )
                # Inject the wrapped adapter into the agent's context
                result = Orchestrator._execute_with_adapter(
                    agent, state, config, wrapped_adapter
                )
                log.debug(f"Finished {agent_name}.execute()")
            return result
        except TimeoutError:
            log.error(f"Timeout during {agent_name} execution")
            # Re-raise timeout errors directly
            raise
        except Exception as e:
            log.error(
                f"Error during {agent_name} execution: {str(e)}",
                exc_info=True,
                extra={"agent": agent_name, "error": str(e)},
            )
            # Wrap agent execution errors in AgentError
            raise AgentError(
                f"Error during agent {agent_name} execution",
                cause=e,
                agent_name=agent_name,
            )

    @staticmethod
    def _handle_agent_completion(
        agent_name: str,
        result: Dict[str, Any],
        state: QueryState,
        metrics: OrchestrationMetrics,
        callbacks: Dict[str, Callable[..., None]],
        duration: float,
        loop: int,
    ) -> None:
        """Handle agent completion (timing, callbacks, logging).

        Args:
            agent_name: Name of the agent
            result: Result of agent execution
            state: Current query state
            metrics: Metrics collector
            callbacks: Callbacks for monitoring execution
            duration: Duration of agent execution
            loop: Current loop number
        """
        # Record timing
        metrics.record_agent_timing(agent_name, duration)

        # Call on_agent_end callback
        if callbacks.get("on_agent_end"):
            log.debug(f"Calling on_agent_end callback for {agent_name}")
            callbacks["on_agent_end"](
                agent_name,
                result,
                state,
            )

        # Log completion with detailed context
        log.info(
            f"Agent {agent_name} completed turn "
            f"(loop {loop + 1}, cycle {state.cycle}) "
            f"in {duration:.2f}s",
            extra={
                "agent": agent_name,
                "loop": loop + 1,
                "cycle": state.cycle,
                "duration": duration,
                "has_claims": "claims" in result and bool(result["claims"]),
                "has_sources": "sources" in result and bool(result["sources"]),
                "result_keys": list(result.keys()),
            },
        )

    @staticmethod
    def _log_sources(agent_name: str, result: Dict[str, Any]) -> None:
        """Log sources with context.

        Args:
            agent_name: Name of the agent
            result: Result of agent execution
        """
        if "sources" in result and result["sources"]:
            source_count = len(result["sources"])
            log.info(
                f"Agent {agent_name} provided {source_count} sources",
                extra={
                    "agent": agent_name,
                    "source_count": source_count,
                    "sources": [
                        s.get("title", "Untitled") if isinstance(s, dict) else str(s)
                        for s in result["sources"][:5]  # Log first 5 sources only
                    ],
                },
            )
        else:
            log.warning(
                f"Agent {agent_name} provided no sources",
                extra={"agent": agent_name, "result_keys": list(result.keys())},
            )

    @staticmethod
    def _persist_claims(
        agent_name: str, result: Dict[str, Any], storage_manager: type[StorageManager]
    ) -> None:
        """Persist claims with error handling.

        Args:
            agent_name: Name of the agent
            result: Result of agent execution
            storage_manager: Storage manager for persisting claims
        """
        try:
            claims = result.get("claims", [])
            if claims:
                log.debug(
                    f"Persisting {len(claims)} claims for agent {agent_name}",
                    extra={"agent": agent_name, "claim_count": len(claims)},
                )
                for i, claim in enumerate(claims):
                    if isinstance(claim, dict) and "id" in claim:
                        log.debug(
                            f"Persisting claim {i + 1}/{len(claims)}: {claim.get('id')}"
                        )
                        storage_manager.persist_claim(claim)
                    else:
                        log.warning(
                            f"Skipping invalid claim format from agent {agent_name}",
                            extra={
                                "agent": agent_name,
                                "claim_index": i,
                                "claim_type": type(claim).__name__,
                                "has_id": isinstance(claim, dict) and "id" in claim,
                            },
                        )
        except Exception as e:
            log.warning(
                f"Error persisting claims for agent {agent_name}: {str(e)}",
                exc_info=True,
                extra={"agent": agent_name, "error": str(e)},
            )
            # Don't fail the whole process for storage errors

    @staticmethod
    def _handle_agent_error(
        agent_name: str, e: Exception, state: QueryState, metrics: OrchestrationMetrics
    ) -> dict:
        """Handle agent errors with granular recovery strategies.

        Args:
            agent_name: Name of the agent
            e: The exception that occurred
            state: Current query state
            metrics: Metrics collector

        Returns:
            Dictionary with error recovery information
        """
        log = get_logger(__name__)

        # Categorize the error for appropriate handling
        error_category = Orchestrator._categorize_error(e)

        # Record detailed error information
        error_info = {
            "agent": agent_name,
            "error": str(e),
            "error_type": type(e).__name__,
            "error_category": error_category,
            "traceback": traceback.format_exc(),
            "timestamp": time.time(),
        }

        # Add to state and metrics
        state.add_error(error_info)
        metrics.record_error(agent_name)

        # Log the error with appropriate level based on category
        if error_category == "critical":
            log.critical(
                f"Critical error during agent {agent_name} execution: {str(e)}",
                exc_info=True,
                extra={"error_info": error_info}
            )
        elif error_category == "recoverable":
            log.error(
                f"Recoverable error during agent {agent_name} execution: {str(e)}",
                exc_info=True,
                extra={"error_info": error_info}
            )
        else:  # "transient"
            log.warning(
                f"Transient error during agent {agent_name} execution: {str(e)}",
                exc_info=True,
                extra={"error_info": error_info}
            )

        # Apply recovery strategy based on error category
        recovery_info = Orchestrator._apply_recovery_strategy(agent_name, error_category, e, state)

        # Update error info with recovery details
        error_info.update(recovery_info)

        # Update circuit breaker state for this agent
        Orchestrator._update_circuit_breaker(agent_name, error_category)

        return error_info

    @staticmethod
    def _categorize_error(e: Exception) -> str:
        """Categorize an error for appropriate handling.

        Args:
            e: The exception to categorize

        Returns:
            Error category: "transient", "recoverable", or "critical"
        """
        # Timeout errors are typically transient
        if isinstance(e, TimeoutError):
            return "transient"

        # Not found errors are typically recoverable
        if isinstance(e, NotFoundError):
            return "recoverable"

        # Agent errors might be recoverable depending on the specific error
        if isinstance(e, AgentError):
            # Check for specific error messages that indicate recoverable errors
            error_str = str(e).lower()
            if any(term in error_str for term in ["retry", "temporary", "timeout", "rate limit"]):
                return "transient"
            elif any(term in error_str for term in ["configuration", "invalid input", "format"]):
                return "recoverable"
            else:
                return "critical"

        # Orchestration errors are typically critical
        if isinstance(e, OrchestrationError):
            return "critical"

        # Default to critical for unknown errors
        return "critical"

    @staticmethod
    def _apply_recovery_strategy(agent_name: str, error_category: str, e: Exception, state: QueryState) -> dict:
        """Apply an appropriate recovery strategy based on error category.

        Args:
            agent_name: Name of the agent
            error_category: Category of the error
            e: The exception that occurred
            state: Current query state

        Returns:
            Dictionary with recovery strategy information
        """
        log = get_logger(__name__)

        if error_category == "transient":
            # For transient errors, we can retry or use a fallback
            recovery_strategy = "retry_with_backoff"
            suggestion = "This error is likely temporary. The system will automatically retry with backoff."

            # Add a placeholder result to avoid breaking the chain
            fallback_result = {
                "claims": [
                    f"Agent {agent_name} encountered a temporary error: {str(e)}"
                ],
                "results": {
                    "fallback": (
                        f"The {agent_name} agent encountered a temporary issue. "
                        "This is likely due to external factors and may resolve on retry."
                    )
                },
                "metadata": {
                    "recovery_applied": True,
                    "recovery_strategy": recovery_strategy,
                },
            }
            state.update(fallback_result)

            log.info(
                f"Applied '{recovery_strategy}' recovery strategy for agent {agent_name}",
                extra={"agent": agent_name, "recovery_strategy": recovery_strategy}
            )

        elif error_category == "recoverable":
            # For recoverable errors, we can use a fallback agent or simplified approach
            recovery_strategy = "fallback_agent"
            suggestion = "This error indicates a configuration or input issue. A fallback approach will be used."

            # Add a simplified result to continue the process
            fallback_result = {
                "claims": [
                    f"Agent {agent_name} encountered a recoverable error: {str(e)}"
                ],
                "results": {
                    "fallback": (
                        f"The {agent_name} agent encountered an issue that prevented it from completing normally. "
                        "A simplified approach has been used instead."
                    )
                },
                "metadata": {
                    "recovery_applied": True,
                    "recovery_strategy": recovery_strategy,
                },
            }
            state.update(fallback_result)

            log.info(
                f"Applied '{recovery_strategy}' recovery strategy for agent {agent_name}",
                extra={"agent": agent_name, "recovery_strategy": recovery_strategy}
            )

        else:  # "critical"
            # For critical errors, we need to fail gracefully
            recovery_strategy = "fail_gracefully"
            suggestion = "This is a critical error that requires attention. Check the logs for details."

            # Add error information to the state
            error_result = {
                "claims": [
                    f"Agent {agent_name} encountered a critical error: {str(e)}"
                ],
                "results": {
                    "error": (
                        f"The {agent_name} agent encountered a critical error that prevented completion. "
                        "This requires investigation."
                    )
                },
                "metadata": {
                    "recovery_applied": True,
                    "recovery_strategy": recovery_strategy,
                    "critical_error": True,
                },
            }
            state.update(error_result)

            log.warning(
                f"Applied '{recovery_strategy}' recovery strategy for agent {agent_name}",
                extra={"agent": agent_name, "recovery_strategy": recovery_strategy}
            )

        return {
            "recovery_strategy": recovery_strategy,
            "suggestion": suggestion
        }

    # Circuit breaker state (class variable)
    _circuit_breakers: dict[str, CircuitBreakerState] = {}

    @staticmethod
    def _update_circuit_breaker(agent_name: str, error_category: str) -> None:
        """Update the circuit breaker state for an agent.

        Implements the circuit breaker pattern to prevent repeated failures.

        Args:
            agent_name: Name of the agent
            error_category: Category of the error
        """
        log = get_logger(__name__)

        # Initialize circuit breaker for this agent if it doesn't exist
        if agent_name not in Orchestrator._circuit_breakers:
            Orchestrator._circuit_breakers[agent_name] = {
                "failure_count": 0.0,
                "last_failure_time": 0.0,
                "state": "closed",  # closed = normal operation, open = failing, half-open = testing recovery
                "recovery_attempts": 0,
            }

        breaker = Orchestrator._circuit_breakers[agent_name]
        current_time = time.time()

        # Update the circuit breaker based on error category
        if error_category in ["critical", "recoverable"]:
            breaker["failure_count"] += 1
            breaker["last_failure_time"] = current_time

            # If we've had too many failures, open the circuit
            if breaker["failure_count"] >= 3 and breaker["state"] == "closed":
                breaker["state"] = "open"
                log.warning(
                    f"Circuit breaker for agent {agent_name} is now OPEN due to repeated failures",
                    extra={"agent": agent_name, "circuit_state": "open", "failure_count": breaker["failure_count"]}
                )

        elif error_category == "transient":
            # For transient errors, we're more lenient
            breaker["failure_count"] += 0.5  # Count transient errors as half failures
            breaker["last_failure_time"] = current_time

        # Check if we should attempt recovery for an open circuit
        if breaker["state"] == "open":
            # After a cooling period (30 seconds), try half-open state
            cooling_period = 30  # seconds
            if current_time - breaker["last_failure_time"] > cooling_period:
                breaker["state"] = "half-open"
                breaker["recovery_attempts"] += 1
                log.info(
                    f"Circuit breaker for agent {agent_name} is now HALF-OPEN, attempting recovery",
                    extra={"agent": agent_name, "circuit_state": "half-open", "recovery_attempts": breaker["recovery_attempts"]}
                )

        # If we're in half-open state and this was a success (not called for an error)
        # This would be called from a success handler, not implemented here

    @staticmethod
    def get_circuit_breaker_state(agent_name: str) -> CircuitBreakerState:
        """Get the current circuit breaker state for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with circuit breaker state information
        """
        if agent_name not in Orchestrator._circuit_breakers:
            return {
                "state": "closed",
                "failure_count": 0.0,
                "last_failure_time": 0.0,
                "recovery_attempts": 0,
            }

        return Orchestrator._circuit_breakers[agent_name].copy()

    @staticmethod
    def _execute_agent(
        agent_name: str,
        state: QueryState,
        config: ConfigModel,
        metrics: OrchestrationMetrics,
        callbacks: Dict[str, Callable[..., None]],
        agent_factory: type[AgentFactory],
        storage_manager: type[StorageManager],
        loop: int,
    ) -> None:
        """Execute a single agent and update state with results.

        Args:
            agent_name: Name of the agent to execute
            state: Current query state
            config: System configuration
            metrics: Metrics collector
            callbacks: Callbacks for monitoring execution
            agent_factory: Factory for creating agent instances
            storage_manager: Storage manager for persisting claims
            loop: Current loop number

        Raises:
            NotFoundError: If agent cannot be found
            AgentError: If agent execution fails
            TimeoutError: If agent execution times out
        """
        try:
            # Get agent instance
            agent = Orchestrator._get_agent(agent_name, agent_factory)

            # Check if agent can execute
            if not Orchestrator._check_agent_can_execute(
                agent, agent_name, state, config
            ):
                return

            # Log agent execution
            Orchestrator._log_agent_execution(agent_name, state, loop)

            # Call on_agent_start callback
            Orchestrator._call_agent_start_callback(agent_name, state, callbacks)

            # Execute agent and measure duration
            start_time = time.time()
            result = Orchestrator._execute_agent_with_token_counting(
                agent, agent_name, state, config, metrics
            )
            duration = time.time() - start_time

            # Handle agent completion
            Orchestrator._handle_agent_completion(
                agent_name, result, state, metrics, callbacks, duration, loop
            )

            # Update state with result
            state.update(result)

            # Log sources
            Orchestrator._log_sources(agent_name, result)

            # Persist claims
            Orchestrator._persist_claims(agent_name, result, storage_manager)

        except Exception as e:
            # Handle agent errors
            Orchestrator._handle_agent_error(agent_name, e, state, metrics)

    @staticmethod
    def _execute_cycle(
        loop: int,
        loops: int,
        agents: List[str],
        primus_index: int,
        max_errors: int,
        state: QueryState,
        config: ConfigModel,
        metrics: OrchestrationMetrics,
        callbacks: Dict[str, Callable[..., None]],
        agent_factory: type[AgentFactory],
        storage_manager: type[StorageManager],
        tracer: Any,
    ) -> int:
        """Execute a single dialectical cycle.

        Args:
            loop: Current loop number
            loops: Total number of loops
            agents: List of agent names
            primus_index: Index of the primus agent
            max_errors: Maximum number of errors before aborting
            state: Current query state
            config: System configuration
            metrics: Metrics collector
            callbacks: Callbacks for monitoring execution
            agent_factory: Factory for creating agent instances
            storage_manager: Storage manager for persisting claims
            tracer: Tracer for distributed tracing

        Returns:
            Updated primus_index for the next cycle
        """
        with tracer.start_as_current_span(
            "cycle",
            attributes={"cycle": loop},
        ):
            log.info(f"Starting loop {loop + 1}/{loops}")
            metrics.start_cycle()

            # Call on_cycle_start callback
            if callbacks.get("on_cycle_start"):
                callbacks["on_cycle_start"](loop, state)

            # Rotate agent order based on primus_index
            order = Orchestrator._rotate_list(agents, primus_index)

            # Execute each agent in order
            for agent_name in order:
                # Skip execution if too many errors
                if state.error_count >= max_errors:
                    log.warning(
                        "Skipping remaining agents due to error threshold "
                        f"({max_errors}) reached"
                    )
                    break

                Orchestrator._execute_agent(
                    agent_name,
                    state,
                    config,
                    metrics,
                    callbacks,
                    agent_factory,
                    storage_manager,
                    loop,
                )

            # End cycle and update metrics
            metrics.end_cycle()
            state.metadata["execution_metrics"] = metrics.get_summary()
            metrics.record_query_tokens(state.query)

            # Prune context to keep state size manageable
            state.prune_context()

            # Call on_cycle_end callback
            if callbacks.get("on_cycle_end"):
                callbacks["on_cycle_end"](loop, state)

            # Check if we need to abort due to errors
            if state.error_count >= max_errors:
                log.error(
                    "Aborting dialectical process due to error "
                    f"threshold reached ({state.error_count}/{max_errors})"
                )
                state.results["error"] = (
                    f"Process aborted after {state.error_count} errors"
                )
                return primus_index

            # Increment cycle counter
            state.cycle += 1

            # Update primus_index for next cycle
            primus_index = (primus_index + 1) % len(agents)
            state.primus_index = primus_index

            return primus_index

    @staticmethod
    async def _execute_cycle_async(
        loop: int,
        loops: int,
        agents: List[str],
        primus_index: int,
        max_errors: int,
        state: QueryState,
        config: ConfigModel,
        metrics: OrchestrationMetrics,
        callbacks: Dict[str, Callable[..., None]],
        agent_factory: type[AgentFactory],
        storage_manager: type[StorageManager],
        tracer: Any,
        *,
        concurrent: bool = False,
    ) -> int:
        """Asynchronous version of ``_execute_cycle``."""
        with tracer.start_as_current_span(
            "cycle",
            attributes={"cycle": loop},
        ):
            log.info(f"Starting loop {loop + 1}/{loops}")
            metrics.start_cycle()

            if callbacks.get("on_cycle_start"):
                callbacks["on_cycle_start"](loop, state)

            order = Orchestrator._rotate_list(agents, primus_index)

            async def run_agent(name: str) -> None:
                if state.error_count >= max_errors:
                    return
                await asyncio.to_thread(
                    Orchestrator._execute_agent,
                    name,
                    state,
                    config,
                    metrics,
                    callbacks,
                    agent_factory,
                    storage_manager,
                    loop,
                )

            if concurrent:
                await asyncio.gather(*(run_agent(a) for a in order))
            else:
                for agent_name in order:
                    if state.error_count >= max_errors:
                        log.warning(
                            "Skipping remaining agents due to error threshold "
                            f"({max_errors}) reached"
                        )
                        break
                    await run_agent(agent_name)

            metrics.end_cycle()
            state.metadata["execution_metrics"] = metrics.get_summary()

            # Prune context to keep state size manageable
            state.prune_context()

            if callbacks.get("on_cycle_end"):
                callbacks["on_cycle_end"](loop, state)

            if state.error_count >= max_errors:
                log.error(
                    "Aborting dialectical process due to error "
                    f"threshold reached ({state.error_count}/{max_errors})"
                )
                state.results["error"] = (
                    f"Process aborted after {state.error_count} errors"
                )
                return primus_index

            state.cycle += 1

            primus_index = (primus_index + 1) % len(agents)
            state.primus_index = primus_index

            return primus_index

    @staticmethod
    def run_query(
        query: str,
        config: ConfigModel,
        callbacks: Dict[str, Callable[..., None]] | None = None,
        *,
        agent_factory: type[AgentFactory] = AgentFactory,
        storage_manager: type[StorageManager] = StorageManager,
    ) -> QueryResponse:
        """Run a query through dialectical agent cycles.

        Args:
            query: The user's query string
            config: System configuration
            callbacks: Optional callbacks for monitoring execution
                Supported callbacks: on_cycle_start, on_cycle_end,
                on_agent_start, on_agent_end
            agent_factory: Factory class used to retrieve agent instances
            storage_manager: Storage manager class for persisting claims

        Returns:
            QueryResponse with answer, citations, reasoning, and metrics
        """
        # Setup tracing and metrics
        setup_tracing(getattr(config, "tracing_enabled", False))
        tracer = get_tracer(__name__)
        record_query()
        metrics = OrchestrationMetrics()
        callbacks = callbacks or {}

        # Parse configuration
        config_params = Orchestrator._parse_config(config)
        agents = config_params["agents"]
        primus_index = config_params["primus_index"]
        loops = config_params["loops"]
        mode = config_params["mode"]
        max_errors = config_params["max_errors"]

        # Adapt token budget based on query complexity and loops
        Orchestrator._apply_adaptive_token_budget(config, query)

        # Scale token budget for parallel agent groups if metadata is present
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
                group_tokens = max(
                    1, token_budget * config.group_size // total_agents
                )
                config.token_budget = group_tokens

        # Adapt token budget based on query complexity
        Orchestrator._apply_adaptive_token_budget(config, query)

        # Heuristically adjust token budget when running within parallel agent
        # groups. ``run_parallel_query`` passes ``group_size`` and
        # ``total_groups`` to ``run_query`` using ``model_copy`` so we can
        # derive a fair token split.
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
                group_tokens = max(
                    1, token_budget * config.group_size // total_agents
                )
                config.token_budget = group_tokens

        # Handle chain-of-thought reasoning mode
        if mode == ReasoningMode.CHAIN_OF_THOUGHT:
            strategy = ChainOfThoughtStrategy()
            return strategy.run_query(
                query,
                config,
                agent_factory=agent_factory,
            )

        # Initialize query state
        state = QueryState(query=query, primus_index=primus_index)

        # Execute dialectical cycles with detailed logging
        log.info(
            f"Starting dialectical process with {len(agents)} agents and {loops} loops",
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

            primus_index = Orchestrator._execute_cycle(
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
            )

            # Break if we need to abort due to errors
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

        # Add final metrics to state
        state.metadata["execution_metrics"] = metrics.get_summary()
        metrics.record_query_tokens(query)

        # Raise error if process aborted or if there were any errors
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

        # Synthesize final response
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
        """Asynchronous wrapper around :meth:`run_query`.

        When ``concurrent`` is ``True`` agents within a cycle are executed
        concurrently using ``asyncio`` threads.
        """

        setup_tracing(getattr(config, "tracing_enabled", False))
        tracer = get_tracer(__name__)
        record_query()
        metrics = OrchestrationMetrics()
        callbacks = callbacks or {}

        config_params = Orchestrator._parse_config(config)
        agents = config_params["agents"]
        primus_index = config_params["primus_index"]
        loops = config_params["loops"]
        mode = config_params["mode"]
        max_errors = config_params["max_errors"]

        # Adapt token budget based on query complexity and loops
        Orchestrator._apply_adaptive_token_budget(config, query)

        # Scale token budget for parallel agent groups if metadata is present
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
                group_tokens = max(
                    1, token_budget * config.group_size // total_agents
                )
                config.token_budget = group_tokens

        if mode == ReasoningMode.CHAIN_OF_THOUGHT:
            strategy = ChainOfThoughtStrategy()
            return await asyncio.to_thread(
                strategy.run_query,
                query,
                config,
                agent_factory=agent_factory,
            )

        state = QueryState(query=query, primus_index=primus_index)

        log.info(
            f"Starting dialectical process with {len(agents)} agents and {loops} loops",
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

            primus_index = await Orchestrator._execute_cycle_async(
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
        query: str, config: ConfigModel, agent_groups: List[List[str]], timeout: int = 300
    ) -> QueryResponse:
        """Run multiple parallel agent groups and synthesize results.

        Args:
            query: The user's query
            config: System configuration
            agent_groups: Lists of agent names to run in parallel
            timeout: Maximum execution time in seconds (default: 300)

        Returns:
            Synthesized QueryResponse from all agent groups
        """
        setup_tracing(getattr(config, "tracing_enabled", False))
        tracer = get_tracer(__name__)
        log = get_logger(__name__)

        # Create a state for the final synthesis
        final_state = QueryState(query=query)

        # Calculate optimal number of workers based on system resources and group count
        cpu_count = os.cpu_count() or 4
        max_workers = min(len(agent_groups), max(1, cpu_count - 1))

        # Track resource usage
        start_time = time.time()
        memory_usage_start = Orchestrator._get_memory_usage()

        # Function to run a single agent group
        total_agents = sum(len(g) for g in agent_groups)

        def run_group(group: List[str]) -> QueryResponse:
            # Create a config copy for this group and annotate it with
            # parallel execution information so ``run_query`` can apply
            # heuristics.
            group_config = config.model_copy(
                update={
                    "agents": group,
                    "group_size": len(group),
                    "total_groups": len(agent_groups),
                    "total_agents": total_agents,
                }
            )

            # Each group initially inherits the full token budget; ``run_query``
            # will scale it based on the provided metadata.
            group_config.token_budget = getattr(config, "token_budget", 4000)

            try:
                # Run the group
                result = Orchestrator.run_query(query, group_config)
                return result
            except Exception as e:
                log.error(f"Error running agent group {group}: {str(e)}", exc_info=True)
                # Re-raise as OrchestrationError
                raise OrchestrationError(
                    f"Error running agent group {group}",
                    cause=e,
                    agent_group=group,
                    suggestion="Check the agent configuration and ensure all agents are properly registered",
                )

        # Run agent groups in parallel
        errors = []
        results = []
        timeouts = []

        with tracer.start_as_current_span("parallel_query") as span:
            span.set_attribute("agent_groups", str(agent_groups))
            span.set_attribute("max_workers", max_workers)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                futures = {executor.submit(run_group, group): group for group in agent_groups}

                # Wait for completion with timeout
                import concurrent.futures
                try:
                    for future in concurrent.futures.as_completed(futures, timeout=timeout):
                        group = futures[future]
                        try:
                            result = future.result()
                            results.append((group, result))
                            log.info(f"Agent group {group} completed successfully")
                            span.add_event(f"Group {group} completed")
                        except Exception as e:
                            errors.append((group, str(e)))
                            log.error(f"Agent group {group} failed: {str(e)}", exc_info=True)
                            span.add_event(f"Group {group} failed", {"error": str(e)})
                except concurrent.futures.TimeoutError:
                    # Handle timeout for remaining futures
                    for future, group in futures.items():
                        if not future.done():
                            future.cancel()
                            timeouts.append(group)
                            log.warning(f"Agent group {group} timed out after {timeout} seconds")
                            span.add_event(f"Group {group} timed out")

            # Record resource usage
            execution_time = time.time() - start_time
            memory_usage_end = Orchestrator._get_memory_usage()
            memory_delta = memory_usage_end - memory_usage_start

            span.set_attribute("execution_time_seconds", execution_time)
            span.set_attribute("memory_usage_delta_mb", memory_delta)

            log.info(
                f"Parallel execution completed in {execution_time:.2f}s with memory delta: {memory_delta:.2f}MB",
                extra={
                    "execution_time": execution_time,
                    "memory_delta": memory_delta,
                    "successful_groups": len(results),
                    "error_groups": len(errors),
                    "timeout_groups": len(timeouts)
                }
            )

        # If all groups failed or timed out, raise an error
        if not results and (errors or timeouts):
            error_details = []
            if errors:
                error_details.extend([f"{group}: {error}" for group, error in errors])
            if timeouts:
                error_details.extend([f"{group}: timed out" for group in timeouts])

            raise OrchestrationError(
                "All parallel agent groups failed or timed out",
                cause=None,
                errors=error_details,
                suggestion="Check the agent configurations and ensure all required agents are properly registered and configured. Consider increasing the timeout value for complex queries.",
            )

        # Merge results into final state with weighting based on agent group performance
        for group, result in results:
            # Calculate a confidence score based on result quality
            confidence = Orchestrator._calculate_result_confidence(result)

            # Convert QueryResponse back to dictionary for state update
            result_dict = {
                "claims": result.reasoning,
                "sources": result.citations,
                "metadata": {
                    **result.metrics,
                    "confidence": confidence,
                    "agent_group": group
                },
                "results": {
                    "group_answer": result.answer,
                    "group_confidence": confidence
                },
            }
            final_state.update(result_dict)

        # Add error and timeout information to final state
        if errors or timeouts:
            error_info = {
                "claims": [],
                "metadata": {
                    "errors": [f"{group}: {error}" for group, error in errors],
                    "timeouts": [f"{group}" for group in timeouts],
                },
            }

            if errors:
                error_info["claims"].extend(
                    [f"Error in agent group {group}: {error}" for group, error in errors]
                )

            if timeouts:
                error_info["claims"].extend(
                    [f"Agent group {group} timed out" for group in timeouts]
                )

            final_state.update(error_info)

        # Create a synthesizer to combine results with weighted aggregation
        synthesizer = AgentFactory.get("Synthesizer")

        # Add aggregation context to help synthesizer combine results effectively
        aggregation_context = {
            "successful_groups": len(results),
            "error_groups": len(errors),
            "timeout_groups": len(timeouts),
            "execution_time": execution_time,
            "aggregation_strategy": "weighted_confidence"
        }
        final_state.update({"metadata": {"aggregation": aggregation_context}})

        final_result = synthesizer.execute(final_state, config)

        # Update state with synthesis
        final_state.update(final_result)

        # Create the final response
        response = final_state.synthesize()

        # Use the synthesizer's answer if available
        if "answer" in final_result and final_result["answer"]:
            response.answer = final_result["answer"]

        # Add detailed execution metrics to response
        response.metrics.update({
            "parallel_execution": {
                "total_groups": len(agent_groups),
                "successful_groups": len(results),
                "error_groups": len(errors),
                "timeout_groups": len(timeouts),
                "execution_time": execution_time,
                "memory_delta_mb": memory_delta
            }
        })

        return response

    @staticmethod
    def _execute_with_adapter(
        agent: Any, state: QueryState, config: ConfigModel, adapter: Any
    ) -> Dict[str, Any]:
        """Execute an agent with a specific adapter.

        This method handles executing an agent with a specific adapter, either by:
        1. Passing the adapter directly to the execute method if it supports it
        2. Temporarily setting the adapter in the agent's context

        Args:
            agent: The agent to execute
            state: The current query state
            config: The system configuration
            adapter: The adapter to use for LLM calls

        Returns:
            The result of agent execution
        """
        # Check if the agent's execute method accepts an adapter parameter
        import inspect

        sig = inspect.signature(agent.execute)

        if "adapter" in sig.parameters:
            # Agent supports direct adapter injection
            return agent.execute(state, config, adapter=adapter)
        elif hasattr(agent, "set_adapter"):
            # Agent supports adapter setting via method
            original_adapter = (
                agent.get_adapter() if hasattr(agent, "get_adapter") else None
            )
            try:
                agent.set_adapter(adapter)
                return agent.execute(state, config)
            finally:
                if original_adapter is not None:
                    agent.set_adapter(original_adapter)
        else:
            # No adapter injection support, just execute normally
            # This won't count tokens, but at least it won't break
            return agent.execute(state, config)

    @staticmethod
    def _rotate_list(items: List[Any], start_idx: int) -> List[Any]:
        """Rotate a list so that start_idx becomes the first element.

        This method is used to reorder the list of agents based on the primus_index,
        ensuring that the primus agent is executed first in each cycle.

        Args:
            items: The list to rotate
            start_idx: The index that should become the first element

        Returns:
            A new list with elements rotated so that items[start_idx] is the first element
        """
        if not items:
            return []
        start_idx = start_idx % len(items)  # Handle index out of bounds
        return items[start_idx:] + items[:start_idx]

    @staticmethod
    def _apply_adaptive_token_budget(config: ConfigModel, query: str) -> None:
        """Adjust ``config.token_budget`` based on query complexity and loops."""

        budget = getattr(config, "token_budget", None)
        if budget is None:
            return

        loops = getattr(config, "loops", 1)
        if loops > 1:
            budget = max(1, budget // loops)

        query_tokens = len(query.split())
        max_budget = query_tokens * 20
        if budget > max_budget:
            config.token_budget = max_budget
        elif budget < query_tokens:
            config.token_budget = query_tokens + 10
        else:
            config.token_budget = budget

    @staticmethod
    def _get_memory_usage() -> float:
        """Get current memory usage in MB.

        Returns:
            Current memory usage in MB
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert to MB
        except ImportError:
            # Fallback if psutil is not available
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Already in KB, convert to MB

    @staticmethod
    def _calculate_result_confidence(result: QueryResponse) -> float:
        """Calculate a confidence score for a query result.

        Args:
            result: The query result to evaluate

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Start with a base confidence
        confidence = 0.5

        # Adjust based on number of citations
        if hasattr(result, 'citations') and result.citations:
            citation_count = len(result.citations)
            # More citations generally indicate better support
            citation_factor = min(0.3, 0.05 * citation_count)
            confidence += citation_factor

        # Adjust based on reasoning length and quality
        if hasattr(result, 'reasoning') and result.reasoning:
            reasoning_length = len(result.reasoning)
            # Longer reasoning chains may indicate more thorough analysis
            # But we cap the bonus to avoid rewarding verbosity
            reasoning_factor = min(0.2, 0.01 * reasoning_length)
            confidence += reasoning_factor

        # Adjust based on token usage efficiency
        if hasattr(result, 'metrics') and 'token_usage' in result.metrics:
            token_usage = result.metrics['token_usage']
            if 'total' in token_usage and 'max_tokens' in token_usage:
                usage_ratio = token_usage['total'] / max(1, token_usage['max_tokens'])
                # Efficient token usage (not too low, not maxed out)
                if 0.3 <= usage_ratio <= 0.9:
                    confidence += 0.1
                elif usage_ratio > 0.9:
                    # Maxed out token usage might indicate truncation
                    confidence -= 0.1

        # Adjust based on execution errors
        if hasattr(result, 'metrics') and 'errors' in result.metrics:
            error_count = len(result.metrics['errors'])
            if error_count > 0:
                # Errors reduce confidence
                confidence -= min(0.4, 0.1 * error_count)

        # Ensure confidence is within bounds
        return max(0.1, min(1.0, confidence))

    @staticmethod
    @contextmanager
    def _capture_token_usage(
        agent_name: str, metrics: OrchestrationMetrics, config: ConfigModel
    ) -> Iterator[tuple[dict[str, int], Any]]:
        """Capture token usage for all LLM calls within the block.

        This method uses the TokenCountingAdapter to count tokens for all LLM calls
        made within the context manager block. It yields a tuple containing a dictionary
        with token counts and the wrapped adapter that should be used for LLM calls.

        Args:
            agent_name: The name of the agent making the LLM calls
            metrics: The metrics collector to record token usage
            config: The system configuration containing the LLM backend

        Yields:
            A tuple containing (token_counter, wrapped_adapter)
        """
        from autoresearch.llm.token_counting import count_tokens
        import autoresearch.llm as llm

        # Get the adapter for the agent using the configured backend
        backend = config.llm_backend
        adapter = llm.get_llm_adapter(backend)
        token_budget = getattr(config, "token_budget", None)

        # Use the count_tokens context manager to count tokens
        # It now returns both the token counter and the wrapped adapter
        with count_tokens(agent_name, adapter, metrics, token_budget) as (
            token_counter,
            wrapped_adapter,
        ):
            yield token_counter, wrapped_adapter

    # --------------------------------------------------------------
    # Storage helper shortcuts
    # --------------------------------------------------------------

    @staticmethod
    def infer_relations() -> None:
        """Infer ontology relations via the storage manager."""
        StorageManager.infer_relations()

    @staticmethod
    def query_ontology(query: str):
        """Query the ontology graph via the storage manager."""
        return StorageManager.query_ontology(query)
