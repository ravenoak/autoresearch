"""
Orchestration system for coordinating multi-agent dialectical cycles.
"""
from typing import List, Dict, Any, Callable
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

log = get_logger(__name__)


class Orchestrator:
    """Coordinates multi-agent dialectical cycles with rotating Primus."""

    @staticmethod
    def run_query(
        query: str,
        config: ConfigModel,
        callbacks: Dict[str, Callable] | None = None,
        *,
        agent_factory: type[AgentFactory] = AgentFactory,
        storage_manager: type[StorageManager] = StorageManager,
    ) -> QueryResponse:
        """Run a query through dialectical agent cycles.

        Args:
            query: The user's query string
            config: System configuration
            callbacks: Optional callbacks for monitoring execution
                Supported: on_cycle_start, on_cycle_end, on_agent_start, on_agent_end
            agent_factory: Factory class used to retrieve agent instances
            storage_manager: Storage manager class for persisting claims

        Returns:
            QueryResponse with answer, citations, reasoning, and metrics
        """
        record_query()
        # Initialize metrics collector
        metrics = OrchestrationMetrics()

        # Setup callbacks
        callbacks = callbacks or {}

        # Get enabled agents and reasoning mode from config
        agents = getattr(config, 'agents', ["Synthesizer", "Contrarian", "FactChecker"])
        primus_index = 0 if not hasattr(config, 'primus_start') else config.primus_start
        loops = config.loops if hasattr(config, 'loops') else 2
        mode = getattr(config, 'reasoning_mode', ReasoningMode.DIALECTICAL)

        if mode == ReasoningMode.DIRECT:
            agents = ["Synthesizer"]
            loops = 1
        elif mode == ReasoningMode.CHAIN_OF_THOUGHT:
            strategy = ChainOfThoughtStrategy()
            return strategy.run_query(query, config, agent_factory=agent_factory)
        max_errors = config.max_errors if hasattr(config, 'max_errors') else 3

        # Initialize query state
        state = QueryState(query=query, primus_index=primus_index)

        # Execute dialectical cycles
        for loop in range(loops):
            log.info(f"Starting loop {loop+1}/{loops}")
            metrics.start_cycle()

            if callbacks.get('on_cycle_start'):
                callbacks['on_cycle_start'](loop, state)

            # Rotate agent order based on primus_index
            order = Orchestrator._rotate_list(agents, primus_index)

            for agent_name in order:
                # Skip execution if too many errors
                if state.error_count >= max_errors:
                    log.warning(f"Skipping remaining agents due to error threshold ({max_errors}) reached")
                    break

                try:
                    agent = agent_factory.get(agent_name)

                    # Check if agent should execute in current state
                    if not agent.can_execute(state, config):
                        log.info(f"Agent {agent_name} skipped execution (can_execute=False)")
                        continue

                    log.info(f"Executing agent: {agent_name}")

                    if callbacks.get('on_agent_start'):
                        callbacks['on_agent_start'](agent_name, state)

                    # Time the execution
                    start_time = time.time()

                    # Execute agent and update state
                    with Orchestrator._capture_token_usage(agent_name, metrics) as _token_counter:
                        result = agent.execute(state, config)
                        # Token counter gets updated in the context manager

                    # Record timing
                    duration = time.time() - start_time
                    metrics.record_agent_timing(agent_name, duration)

                    if callbacks.get('on_agent_end'):
                        callbacks['on_agent_end'](agent_name, result, state)

                    # Log agent output
                    log.info(f"Agent {agent_name} completed turn (loop {loop+1}, cycle {state.cycle}) in {duration:.2f}s")

                    # Update shared state
                    state.update(result)

                    # Check for source metadata
                    if "sources" in result and result["sources"]:
                        log.info(f"Agent {agent_name} provided {len(result['sources'])} sources")
                    else:
                        log.warning(f"Agent {agent_name} provided no sources")

                    # Persist any claims to storage
                    for claim in result.get("claims", []):
                        if isinstance(claim, dict) and "id" in claim:
                            storage_manager.persist_claim(claim)

                except Exception as e:
                    error_info = {
                        "agent": agent_name,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                        "timestamp": time.time()
                    }
                    state.add_error(error_info)
                    metrics.record_error(agent_name)
                    log.error(f"Error during agent {agent_name} execution: {str(e)}", exc_info=True)

            # End cycle and record metrics
            metrics.end_cycle()
            # Update state with current metrics so callbacks can display them
            state.metadata["execution_metrics"] = metrics.get_summary()

            if callbacks.get('on_cycle_end'):
                callbacks['on_cycle_end'](loop, state)

            # Check if we should abort due to errors
            if state.error_count >= max_errors:
                log.error(f"Aborting dialectical process due to error threshold reached ({state.error_count}/{max_errors})")
                # Add error information to results
                state.results["error"] = f"Process aborted after {state.error_count} errors"
                break

            # Increment cycle counter
            state.cycle += 1

            # Rotate primus for next loop
            primus_index = (primus_index + 1) % len(agents)
            state.primus_index = primus_index

        # Add metrics to state
        state.metadata["execution_metrics"] = metrics.get_summary()

        # Synthesize final response
        return state.synthesize()

    @staticmethod
    def run_parallel_query(query: str, config: ConfigModel,
                           agent_groups: List[List[str]]) -> QueryResponse:
        """Run multiple parallel agent groups and synthesize results.

        Args:
            query: The user's query
            config: System configuration
            agent_groups: Lists of agent names to run in parallel

        Returns:
            Synthesized QueryResponse from all agent groups
        """
        # Create a state for the final synthesis
        final_state = QueryState(query=query)

        # Function to run a single agent group
        def run_group(group):
            # Create a config copy for this group
            group_config = config.model_copy()
            group_config.agents = group

            # Run the group
            result = Orchestrator.run_query(query, group_config)
            return result

        # Run agent groups in parallel
        with ThreadPoolExecutor(max_workers=min(len(agent_groups), 4)) as executor:
            results = list(executor.map(run_group, agent_groups))

        # Merge results into final state
        for result in results:
            # Convert QueryResponse back to dictionary for state update
            result_dict = {
                "claims": result.reasoning,
                "sources": result.citations,
                "metadata": result.metrics,
                "results": {"group_answer": result.answer}
            }
            final_state.update(result_dict)

        # Create a synthesizer to combine results
        synthesizer = AgentFactory.get("Synthesizer")
        final_result = synthesizer.execute(final_state, config)

        # Update state with synthesis
        final_state.update(final_result)

        # Return final response
        return final_state.synthesize()

    @staticmethod
    def _rotate_list(items: List[Any], start_idx: int) -> List[Any]:
        """Rotate a list so that start_idx becomes the first element."""
        if not items:
            return []
        start_idx = start_idx % len(items)  # Handle index out of bounds
        return items[start_idx:] + items[:start_idx]

    @staticmethod
    @contextmanager
    def _capture_token_usage(agent_name: str, metrics: OrchestrationMetrics):
        """Context manager to capture token usage during agent execution."""
        # This would be connected to the actual token counting logic
        # of the LLM backend in a real implementation
        token_counter = {"in": 0, "out": 0}

        try:
            yield token_counter
        finally:
            # Record tokens in metrics
            metrics.record_tokens(agent_name, token_counter["in"], token_counter["out"])
