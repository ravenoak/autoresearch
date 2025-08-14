from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List

import rdflib

from ..agents.registry import AgentFactory
from ..config.models import ConfigModel
from ..errors import (
    AgentError,
    NotFoundError,
    OrchestrationError,
    StorageError,
    TimeoutError,
)
from ..logging_utils import get_logger
from ..storage import StorageManager
from .circuit_breaker import CircuitBreakerManager
from .error_handling import _handle_agent_error
from .metrics import OrchestrationMetrics
from .state import QueryState
from .token_utils import _capture_token_usage as capture_token_usage
from .token_utils import _execute_with_adapter as execute_with_adapter

log = get_logger(__name__)


def _get_agent(agent_name: str, agent_factory: type[AgentFactory]) -> Any:
    """Get an agent instance from the factory."""
    try:
        return agent_factory.get(agent_name)
    except Exception as e:  # pragma: no cover - defensive
        raise NotFoundError(
            f"Agent '{agent_name}' not found",
            resource_type="agent",
            resource_id=agent_name,
            cause=e,
        )


def _check_agent_can_execute(
    agent: Any, agent_name: str, state: QueryState, config: ConfigModel
) -> bool:
    """Check if an agent can execute."""
    if not agent.can_execute(state, config):
        log.info(f"Agent {agent_name} skipped execution (can_execute=False)")
        return False
    return True


def _log_agent_execution(agent_name: str, state: QueryState, loop: int) -> None:
    """Log agent execution start."""
    log.info(
        f"Executing agent: {agent_name} (loop {loop + 1}, cycle {state.cycle})",
        extra={
            "agent": agent_name,
            "loop": loop + 1,
            "cycle": state.cycle,
            "query": state.query[:100] + "..." if len(state.query) > 100 else state.query,
        },
    )


def _deliver_messages(agent_name: str, state: QueryState, config: ConfigModel) -> None:
    """Record messages destined for the given agent."""
    if not getattr(config, "enable_agent_messages", False):
        return
    msgs = state.get_messages(recipient=agent_name)
    if not msgs:
        return
    delivered = state.metadata.setdefault("delivered_messages", {}).setdefault(
        agent_name, []
    )
    delivered.extend(msgs)
    log.debug(
        f"Delivered {len(msgs)} messages to {agent_name}",
        extra={"agent": agent_name, "message_count": len(msgs)},
    )


def _call_agent_start_callback(
    agent_name: str, state: QueryState, callbacks: Dict[str, Callable[..., None]]
) -> None:
    """Call the on_agent_start callback if it exists."""
    if callbacks.get("on_agent_start"):
        log.debug(f"Calling on_agent_start callback for {agent_name}")
        callbacks["on_agent_start"](agent_name, state)


def _execute_agent_with_token_counting(
    agent: Any,
    agent_name: str,
    state: QueryState,
    config: ConfigModel,
    metrics: OrchestrationMetrics,
) -> Dict[str, Any]:
    """Execute an agent with token counting."""
    try:
        log.debug(f"Starting token counting for {agent_name}")
        with capture_token_usage(agent_name, metrics, config) as (
            token_counter,
            wrapped_adapter,
        ):
            log.debug(
                f"Executing {agent_name}.execute() with token counting adapter"
            )
            result = execute_with_adapter(agent, state, config, wrapped_adapter)
            log.debug(f"Finished {agent_name}.execute()")
        return result
    except TimeoutError:
        log.error(f"Timeout during {agent_name} execution")
        raise
    except AgentError as e:
        log.error(
            f"Error during {agent_name} execution: {str(e)}",
            exc_info=True,
            extra={"agent": agent_name, "error": str(e)},
        )
        raise


def _handle_agent_completion(
    agent_name: str,
    result: Dict[str, Any],
    state: QueryState,
    metrics: OrchestrationMetrics,
    callbacks: Dict[str, Callable[..., None]],
    duration: float,
    loop: int,
) -> None:
    """Handle agent completion (timing, callbacks, logging)."""
    metrics.record_agent_timing(agent_name, duration)
    if callbacks.get("on_agent_end"):
        log.debug(f"Calling on_agent_end callback for {agent_name}")
        callbacks["on_agent_end"](agent_name, result, state)
    log.info(
        f"Agent {agent_name} completed turn (loop {loop + 1}, cycle {state.cycle}) in {duration:.2f}s",
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


def _log_sources(agent_name: str, result: Dict[str, Any]) -> None:
    """Log sources with context."""
    if "sources" in result and result["sources"]:
        source_count = len(result["sources"])
        log.info(
            f"Agent {agent_name} provided {source_count} sources",
            extra={
                "agent": agent_name,
                "source_count": source_count,
                "sources": [
                    s.get("title", "Untitled") if isinstance(s, dict) else str(s)
                    for s in result["sources"][:5]
                ],
            },
        )
    else:
        log.warning(
            f"Agent {agent_name} provided no sources",
            extra={"agent": agent_name, "result_keys": list(result.keys())},
        )


def _persist_claims(
    agent_name: str, result: Dict[str, Any], storage_manager: type[StorageManager]
) -> None:
    """Persist claims with error handling."""
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
    except (StorageError, rdflib.exceptions.Error, ValueError) as e:
        log.warning(
            f"Error persisting claims for agent {agent_name}: {str(e)}",
            exc_info=True,
            extra={"agent": agent_name, "error": str(e)},
        )


def _execute_agent(
    agent_name: str,
    state: QueryState,
    config: ConfigModel,
    metrics: OrchestrationMetrics,
    callbacks: Dict[str, Callable[..., None]],
    agent_factory: type[AgentFactory],
    storage_manager: type[StorageManager],
    loop: int,
    cb_manager: CircuitBreakerManager,
) -> None:
    """Execute a single agent and update state with results."""
    retries = getattr(config, "retry_attempts", 1)
    backoff = getattr(config, "retry_backoff", 0.0)
    breaker_state = cb_manager.get_circuit_breaker_state(agent_name)
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
        metrics.record_circuit_breaker(agent_name, breaker_state)
        return
    for attempt in range(retries):
        try:
            agent = _get_agent(agent_name, agent_factory)
            if not _check_agent_can_execute(agent, agent_name, state, config):
                return
            _deliver_messages(agent_name, state, config)
            _log_agent_execution(agent_name, state, loop)
            _call_agent_start_callback(agent_name, state, callbacks)
            start_time = time.time()
            result = _execute_agent_with_token_counting(
                agent, agent_name, state, config, metrics
            )
            duration = time.time() - start_time
            _handle_agent_completion(
                agent_name, result, state, metrics, callbacks, duration, loop
            )
            state.update(result)
            _log_sources(agent_name, result)
            _persist_claims(agent_name, result, storage_manager)
            cb_manager.handle_agent_success(agent_name)
            metrics.record_circuit_breaker(
                agent_name, cb_manager.get_circuit_breaker_state(agent_name)
            )
            return
        except (
            AgentError,
            TimeoutError,
            NotFoundError,
            OrchestrationError,
            ValueError,
            RuntimeError,
        ) as e:
            error_info = _handle_agent_error(agent_name, e, state, metrics)
            state.add_error(error_info)
            category = str(error_info.get("error_category", "critical"))
            cb_manager.update_circuit_breaker(agent_name, category)
            metrics.record_circuit_breaker(
                agent_name, cb_manager.get_circuit_breaker_state(agent_name)
            )
            if (
                attempt < retries - 1
                and error_info.get("error_category") == "transient"
            ):
                sleep_time = backoff * (2**attempt)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                continue
            break


def _rotate_list(items: List[Any], start_idx: int) -> List[Any]:
    """Rotate a list so that start_idx becomes the first element."""
    if not items:
        return []
    start_idx = start_idx % len(items)
    return items[start_idx:] + items[:start_idx]


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
    cb_manager: CircuitBreakerManager,
) -> int:
    """Execute a single dialectical cycle."""
    with tracer.start_as_current_span(
        "cycle",
        attributes={"cycle": loop},
    ):
        log.info(f"Starting loop {loop + 1}/{loops}")
        metrics.start_cycle()
        if callbacks.get("on_cycle_start"):
            callbacks["on_cycle_start"](loop, state)
        order = _rotate_list(agents, primus_index)
        for group in order:
            for agent_name in group:
                if state.error_count >= max_errors:
                    log.warning(
                        "Skipping remaining agents due to error threshold "
                        f"({max_errors}) reached"
                    )
                    break
                _execute_agent(
                    agent_name,
                    state,
                    config,
                    metrics,
                    callbacks,
                    agent_factory,
                    storage_manager,
                    loop,
                    cb_manager,
                )
            if state.error_count >= max_errors:
                break
        metrics.end_cycle()
        state.metadata["execution_metrics"] = metrics.get_summary()
        metrics.record_query_tokens(state.query)
        token_budget = getattr(config, "token_budget", None)
        if token_budget is not None:
            config.token_budget = metrics.suggest_token_budget(token_budget)
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
    cb_manager: CircuitBreakerManager,
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
        order = _rotate_list(agents, primus_index)

        async def run_agent(name: str) -> None:
            if state.error_count >= max_errors:
                return
            await asyncio.to_thread(
                _execute_agent,
                name,
                state,
                config,
                metrics,
                callbacks,
                agent_factory,
                storage_manager,
                loop,
                cb_manager,
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
