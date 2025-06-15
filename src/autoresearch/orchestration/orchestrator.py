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

from typing import List, Dict, Any, Callable, Iterator, cast
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

from ..agents.registry import AgentFactory
from ..config import ConfigModel
from .reasoning import ReasoningMode, ChainOfThoughtStrategy
from ..models import QueryResponse
from ..storage import StorageManager
from .state import QueryState
from .metrics import OrchestrationMetrics, record_query
from ..logging_utils import get_logger
from ..tracing import setup_tracing, get_tracer
from ..errors import (
    OrchestrationError, 
    AgentError, 
    NotFoundError, 
    TimeoutError
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
        primus_index = (
            0 if not hasattr(config, "primus_start") else config.primus_start
        )
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
                cause=e
            )

    @staticmethod
    def _check_agent_can_execute(agent: Any, agent_name: str, state: QueryState, config: ConfigModel) -> bool:
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
            log.info(
                f"Agent {agent_name} skipped execution "
                "(can_execute=False)"
            )
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
            f"Executing agent: {agent_name} (loop {loop+1}, cycle {state.cycle})",
            extra={
                "agent": agent_name,
                "loop": loop+1,
                "cycle": state.cycle,
                "query": state.query[:100] + "..." if len(state.query) > 100 else state.query
            }
        )

    @staticmethod
    def _call_agent_start_callback(agent_name: str, state: QueryState, callbacks: Dict[str, Callable[..., None]]) -> None:
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
        metrics: OrchestrationMetrics
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
            with Orchestrator._capture_token_usage(
                agent_name, metrics, config
            ) as (token_counter, wrapped_adapter):
                log.debug(f"Executing {agent_name}.execute() with token counting adapter")
                # Inject the wrapped adapter into the agent's context
                result = Orchestrator._execute_with_adapter(agent, state, config, wrapped_adapter)
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
                extra={"agent": agent_name, "error": str(e)}
            )
            # Wrap agent execution errors in AgentError
            raise AgentError(
                f"Error during agent {agent_name} execution",
                cause=e,
                agent_name=agent_name
            )

    @staticmethod
    def _handle_agent_completion(
        agent_name: str, 
        result: Dict[str, Any], 
        state: QueryState, 
        metrics: OrchestrationMetrics, 
        callbacks: Dict[str, Callable[..., None]], 
        duration: float, 
        loop: int
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
            f"(loop {loop+1}, cycle {state.cycle}) "
            f"in {duration:.2f}s",
            extra={
                "agent": agent_name,
                "loop": loop+1,
                "cycle": state.cycle,
                "duration": duration,
                "has_claims": "claims" in result and bool(result["claims"]),
                "has_sources": "sources" in result and bool(result["sources"]),
                "result_keys": list(result.keys())
            }
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
                    ]
                }
            )
        else:
            log.warning(
                f"Agent {agent_name} provided no sources",
                extra={"agent": agent_name, "result_keys": list(result.keys())}
            )

    @staticmethod
    def _persist_claims(agent_name: str, result: Dict[str, Any], storage_manager: type[StorageManager]) -> None:
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
                    extra={"agent": agent_name, "claim_count": len(claims)}
                )
                for i, claim in enumerate(claims):
                    if isinstance(claim, dict) and "id" in claim:
                        log.debug(f"Persisting claim {i+1}/{len(claims)}: {claim.get('id')}")
                        storage_manager.persist_claim(claim)
                    else:
                        log.warning(
                            f"Skipping invalid claim format from agent {agent_name}",
                            extra={
                                "agent": agent_name,
                                "claim_index": i,
                                "claim_type": type(claim).__name__,
                                "has_id": isinstance(claim, dict) and "id" in claim
                            }
                        )
        except Exception as e:
            log.warning(
                f"Error persisting claims for agent {agent_name}: {str(e)}",
                exc_info=True,
                extra={"agent": agent_name, "error": str(e)}
            )
            # Don't fail the whole process for storage errors

    @staticmethod
    def _handle_agent_error(agent_name: str, e: Exception, state: QueryState, metrics: OrchestrationMetrics) -> None:
        """Handle agent errors.

        Args:
            agent_name: Name of the agent
            e: The exception that occurred
            state: Current query state
            metrics: Metrics collector
        """
        # Record error information
        error_info = {
            "agent": agent_name,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": time.time(),
        }
        state.add_error(error_info)
        metrics.record_error(agent_name)
        log.error(
            f"Error during agent {agent_name} execution: "
            f"{str(e)}",
            exc_info=True,
        )

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
            if not Orchestrator._check_agent_can_execute(agent, agent_name, state, config):
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
            log.info(f"Starting loop {loop+1}/{loops}")
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
                "reasoning_mode": str(mode)
            }
        )

        for loop in range(loops):
            log.debug(
                f"Starting loop {loop+1}/{loops} with primus_index {primus_index}",
                extra={"loop": loop+1, "total_loops": loops, "primus_index": primus_index}
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
                    extra={"error": state.results["error"], "error_count": state.error_count}
                )
                break

            log.debug(
                f"Completed loop {loop+1}/{loops}, new primus_index: {primus_index}",
                extra={
                    "loop": loop+1,
                    "total_loops": loops,
                    "primus_index": primus_index,
                    "cycle": state.cycle,
                    "error_count": state.error_count
                }
            )

        # Add final metrics to state
        state.metadata["execution_metrics"] = metrics.get_summary()

        # Raise error if process aborted or if there were any errors
        if "error" in state.results or state.error_count > 0:
            error_message = state.results.get("error", f"Process completed with {state.error_count} errors")
            raise OrchestrationError(
                error_message, 
                cause=None,
                errors=state.metadata.get("errors", []),
                suggestion="Check the agent execution logs for details on the specific error and ensure all agents are properly configured"
            )

        # Synthesize final response
        return state.synthesize()

    @staticmethod
    def run_parallel_query(
        query: str, config: ConfigModel, agent_groups: List[List[str]]
    ) -> QueryResponse:
        """Run multiple parallel agent groups and synthesize results.

        Args:
            query: The user's query
            config: System configuration
            agent_groups: Lists of agent names to run in parallel

        Returns:
            Synthesized QueryResponse from all agent groups
        """
        setup_tracing(getattr(config, "tracing_enabled", False))
        tracer = get_tracer(__name__)

        # Create a state for the final synthesis
        final_state = QueryState(query=query)

        # Function to run a single agent group
        def run_group(group: List[str]) -> QueryResponse:
            # Create a config copy for this group
            group_config = config.model_copy()
            group_config.agents = group

            try:
                # Run the group
                result = Orchestrator.run_query(query, group_config)
                return result
            except Exception as e:
                log.error(
                    f"Error running agent group {group}: {str(e)}",
                    exc_info=True
                )
                # Re-raise as OrchestrationError
                raise OrchestrationError(
                    f"Error running agent group {group}",
                    cause=e,
                    agent_group=group,
                    suggestion="Check the agent configuration and ensure all agents are properly registered"
                )

        # Run agent groups in parallel
        errors = []
        results = []

        with tracer.start_as_current_span("parallel_query"):
            with ThreadPoolExecutor(
                max_workers=min(len(agent_groups), 4)
            ) as executor:
                # Submit all tasks
                futures = [executor.submit(run_group, group) for group in agent_groups]

                # Collect results and errors
                for future in futures:
                    try:
                        results.append(future.result())
                    except Exception as e:
                        errors.append(str(e))
                        log.error(f"Parallel execution error: {str(e)}", exc_info=True)

        # If all groups failed, raise an error
        if not results and errors:
            raise OrchestrationError(
                "All parallel agent groups failed",
                cause=None,
                errors=errors,
                suggestion="Check the agent configurations and ensure all required agents are properly registered and configured"
            )

        # Merge results into final state
        for result in results:
            # Convert QueryResponse back to dictionary for state update
            result_dict = {
                "claims": result.reasoning,
                "sources": result.citations,
                "metadata": result.metrics,
                "results": {"group_answer": result.answer},
            }
            final_state.update(result_dict)

        # Add error information to final state if there were errors
        if errors:
            error_info = {
                "claims": [f"Error in parallel execution: {error}" for error in errors],
                "metadata": {"errors": errors},
                "results": {"error": f"Some agent groups failed: {', '.join(errors)}"}
            }
            final_state.update(error_info)

        # Create a synthesizer to combine results
        synthesizer = AgentFactory.get("Synthesizer")
        final_result = synthesizer.execute(final_state, config)

        # Update state with synthesis
        final_state.update(final_result)

        # Create the final response
        response = final_state.synthesize()

        # Use the synthesizer's answer if available
        if "answer" in final_result and final_result["answer"]:
            response.answer = final_result["answer"]

        return response

    @staticmethod
    def _execute_with_adapter(agent: Any, state: QueryState, config: ConfigModel, adapter: Any) -> Dict[str, Any]:
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

        if 'adapter' in sig.parameters:
            # Agent supports direct adapter injection
            return agent.execute(state, config, adapter=adapter)
        elif hasattr(agent, 'set_adapter'):
            # Agent supports adapter setting via method
            original_adapter = agent.get_adapter() if hasattr(agent, 'get_adapter') else None
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

        # Use the count_tokens context manager to count tokens
        # It now returns both the token counter and the wrapped adapter
        with count_tokens(agent_name, adapter, metrics) as (token_counter, wrapped_adapter):
            yield token_counter, wrapped_adapter
