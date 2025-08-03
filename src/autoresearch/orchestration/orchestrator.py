"""
Orchestration system for coordinating multi-agent dialectical cycles.

This module currently serves as a prototype for future orchestration work and
has only minimal automated test coverage.  Interfaces may change.

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

from typing import (
    List,
    Dict,
    Any,
    Callable,
    ContextManager,
)
import time
import traceback
import asyncio

from ..agents.registry import AgentFactory, AgentRegistry
from ..config.models import ConfigModel
from .reasoning import ReasoningMode, ChainOfThoughtStrategy
from ..models import QueryResponse
from ..storage import StorageManager
from .state import QueryState
from .metrics import OrchestrationMetrics, record_query
from .token_utils import (
    _capture_token_usage as capture_token_usage,
    _execute_with_adapter as execute_with_adapter,
)
from ..logging_utils import get_logger
from ..tracing import setup_tracing, get_tracer
from ..errors import OrchestrationError, AgentError, NotFoundError, TimeoutError
import rdflib

from . import circuit_breaker
from .circuit_breaker import (
    CircuitBreakerState,
    update_circuit_breaker,
    handle_agent_success,
    get_circuit_breaker_state,
    _circuit_breakers,
)


log = get_logger(__name__)


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
        cb_threshold = getattr(config, "circuit_breaker_threshold", 3)
        cb_cooldown = getattr(config, "circuit_breaker_cooldown", 30)
        retry_attempts = getattr(config, "retry_attempts", 1)
        retry_backoff = getattr(config, "retry_backoff", 0.0)
        enable_messages = getattr(config, "enable_agent_messages", False)
        coalitions = getattr(config, "coalitions", {})
        for cname, members in coalitions.items():
            AgentRegistry.create_coalition(cname, members)
        enable_feedback = getattr(config, "enable_feedback", False)

        # Adjust parameters based on reasoning mode
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
    def _deliver_messages(agent_name: str, state: QueryState, config: ConfigModel) -> None:
        """Record messages destined for the given agent."""

        if not getattr(config, "enable_agent_messages", False):
            return

        msgs = state.get_messages(recipient=agent_name)
        if not msgs:
            return
        delivered = state.metadata.setdefault("delivered_messages", {}).setdefault(agent_name, [])
        delivered.extend(msgs)
        log.debug(
            f"Delivered {len(msgs)} messages to {agent_name}",
            extra={"agent": agent_name, "message_count": len(msgs)},
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

        # Record metrics
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

    # Circuit breaker configuration and state (delegated to circuit_breaker module)
    _circuit_breakers: dict[str, CircuitBreakerState] = _circuit_breakers

    @staticmethod
    def _update_circuit_breaker(agent_name: str, error_category: str) -> None:
        """Delegate circuit breaker updates to :mod:`circuit_breaker`."""
        update_circuit_breaker(agent_name, error_category)

    @staticmethod
    def _handle_agent_success(agent_name: str) -> None:
        """Delegate circuit breaker success handling to :mod:`circuit_breaker`."""
        handle_agent_success(agent_name)

    @staticmethod
    def get_circuit_breaker_state(agent_name: str) -> CircuitBreakerState:
        """Delegate retrieval of circuit breaker state."""
        return get_circuit_breaker_state(agent_name)

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
        retries = getattr(config, "retry_attempts", 1)
        backoff = getattr(config, "retry_backoff", 0.0)

        breaker_state = Orchestrator.get_circuit_breaker_state(agent_name)
        if breaker_state.get("state") == "open":
            error_info = {
                "agent": agent_name,
                "error": "Circuit breaker open",
                "error_type": "CircuitBreakerOpen",
                "error_category": "critical",
                "traceback": "",
                "timestamp": time.time(),
            }
            state.add_error(error_info)
            metrics.record_error(agent_name)
            metrics.record_circuit_breaker(agent_name)
            return

        for attempt in range(retries):
            try:
                # Get agent instance
                agent = Orchestrator._get_agent(agent_name, agent_factory)

                # Check if agent can execute
                if not Orchestrator._check_agent_can_execute(
                    agent, agent_name, state, config
                ):
                    return

                # Deliver pending messages to this agent for the current cycle
                Orchestrator._deliver_messages(agent_name, state, config)

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

                # Successful execution resets circuit breaker state
                Orchestrator._handle_agent_success(agent_name)
                metrics.record_circuit_breaker(agent_name)
                return
            except Exception as e:
                error_info = Orchestrator._handle_agent_error(
                    agent_name, e, state, metrics
                )
                state.add_error(error_info)
                category = str(error_info.get("error_category", "critical"))
                Orchestrator._update_circuit_breaker(agent_name, category)
                metrics.record_circuit_breaker(agent_name)

                # Retry for transient errors if attempts remain
                if (
                    attempt < retries - 1
                    and error_info.get("error_category") == "transient"
                ):
                    sleep_time = backoff * (2 ** attempt)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    continue
                break

    @staticmethod
    def _execute_cycle(
        loop: int,
        loops: int,
        agents: List[List[str]],
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
            agents: Groups of agent names
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

            # Execute each agent group in order
            for group in order:
                for agent_name in group:
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
                if state.error_count >= max_errors:
                    break

            # End cycle and update metrics
            metrics.end_cycle()
            state.metadata["execution_metrics"] = metrics.get_summary()
            metrics.record_query_tokens(state.query)
            token_budget = getattr(config, "token_budget", None)
            if token_budget is not None:
                config.token_budget = metrics.suggest_token_budget(token_budget)

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
        agents: List[List[str]],
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
                for group in order:
                    await asyncio.gather(*(run_agent(a) for a in group))
                    if state.error_count >= max_errors:
                        break
            else:
                for group in order:
                    for agent_name in group:
                        if state.error_count >= max_errors:
                            log.warning(
                                "Skipping remaining agents due to error threshold "
                                f"({max_errors}) reached"
                            )
                            break
                        await run_agent(agent_name)
                    if state.error_count >= max_errors:
                        break

            metrics.end_cycle()
            state.metadata["execution_metrics"] = metrics.get_summary()
            token_budget = getattr(config, "token_budget", None)
            if token_budget is not None:
                config.token_budget = metrics.suggest_token_budget(token_budget)

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
        agents = config_params["agent_groups"]
        primus_index = config_params["primus_index"]
        loops = config_params["loops"]
        mode = config_params["mode"]
        max_errors = config_params["max_errors"]
        circuit_breaker._circuit_breaker_threshold = config_params["circuit_breaker_threshold"]
        circuit_breaker._circuit_breaker_cooldown = config_params["circuit_breaker_cooldown"]

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

        # Handle chain-of-thought reasoning mode
        if mode == ReasoningMode.CHAIN_OF_THOUGHT:
            strategy = ChainOfThoughtStrategy()
            return strategy.run_query(
                query,
                config,
                agent_factory=agent_factory,
            )

        # Initialize query state
        state = QueryState(
            query=query,
            primus_index=primus_index,
            coalitions=config_params.get("coalitions", {}),
        )

        # Execute dialectical cycles with detailed logging
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
        agents = config_params["agent_groups"]
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
        """Run multiple parallel agent groups and synthesize results."""
        from . import parallel

        return parallel.execute_parallel_query(query, config, agent_groups, timeout)

    @staticmethod
    def _execute_with_adapter(
        agent: Any, state: QueryState, config: ConfigModel, adapter: Any
    ) -> Dict[str, Any]:
        """Execute an agent with a specific adapter."""
        return execute_with_adapter(agent, state, config, adapter)

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
        factor = getattr(config, "adaptive_max_factor", 20)
        buffer = getattr(config, "adaptive_min_buffer", 10)
        max_budget = query_tokens * factor
        if budget > max_budget:
            config.token_budget = max_budget
        elif budget < query_tokens:
            config.token_budget = query_tokens + buffer
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
    def _capture_token_usage(
        agent_name: str, metrics: OrchestrationMetrics, config: ConfigModel
    ) -> ContextManager[tuple[dict[str, int], Any]]:
        """Capture token usage for all LLM calls within the block."""
        return capture_token_usage(agent_name, metrics, config)

    # --------------------------------------------------------------
    # Storage helper shortcuts
    # --------------------------------------------------------------

    @staticmethod
    def infer_relations() -> None:
        """Infer ontology relations via the storage manager."""
        StorageManager.infer_relations()

    @staticmethod
    def query_ontology(query: str) -> rdflib.query.Result:
        """Query the ontology graph via the storage manager."""
        return StorageManager.query_ontology(query)
