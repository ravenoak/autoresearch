"""Parallel execution helpers for agent groups."""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple

from ..config.models import ConfigModel
from ..models import QueryResponse
from .state import QueryState
from ..agents.registry import AgentFactory
from ..errors import AgentError, OrchestrationError, TimeoutError
from ..logging_utils import get_logger
from ..tracing import get_tracer, setup_tracing


log = get_logger(__name__)


def _get_memory_usage() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil  # type: ignore

        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)
    except ImportError:  # pragma: no cover - fallback path
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _calculate_result_confidence(result: QueryResponse) -> float:
    """Compute a naive confidence score for a query result."""
    confidence = 0.5

    if getattr(result, "citations", None):
        citation_count = len(result.citations)
        confidence += min(0.3, 0.05 * citation_count)

    if getattr(result, "reasoning", None):
        reasoning_length = len(result.reasoning)
        confidence += min(0.2, 0.01 * reasoning_length)

    if getattr(result, "metrics", None) and "token_usage" in result.metrics:
        tokens = result.metrics["token_usage"]
        if "total" in tokens and "max_tokens" in tokens:
            ratio = tokens["total"] / max(1, tokens["max_tokens"])
            if 0.3 <= ratio <= 0.9:
                confidence += 0.1
            elif ratio > 0.9:
                confidence -= 0.1

    if getattr(result, "metrics", None) and "errors" in result.metrics:
        error_count = len(result.metrics["errors"])
        if error_count > 0:
            confidence -= min(0.4, 0.1 * error_count)

    return max(0.1, min(1.0, confidence))


def execute_parallel_query(
    query: str,
    config: ConfigModel,
    agent_groups: List[List[str]],
    timeout: int = 300,
) -> QueryResponse:
    """Run multiple agent groups in parallel and synthesize results."""

    setup_tracing(getattr(config, "tracing_enabled", False))
    tracer = get_tracer(__name__)
    log = get_logger(__name__)

    final_state = QueryState(query=query, coalitions=getattr(config, "coalitions", {}))

    cpu_count = os.cpu_count() or 4
    max_workers = min(len(agent_groups), max(1, cpu_count - 1))

    start_time = time.time()
    memory_usage_start = _get_memory_usage()

    total_agents = sum(len(g) for g in agent_groups)

    def run_group(group: List[str]) -> QueryResponse:
        from .orchestrator import Orchestrator

        group_config = config.model_copy(
            update={
                "agents": group,
                "group_size": len(group),
                "total_groups": len(agent_groups),
                "total_agents": total_agents,
            }
        )
        group_config.token_budget = getattr(config, "token_budget", 4000)

        try:
            return Orchestrator.run_query(query, group_config)
        except (
            AgentError,
            TimeoutError,
            OrchestrationError,
            ValueError,
            RuntimeError,
        ) as e:
            log.error(f"Error running agent group {group}: {e}", exc_info=True)
            raise OrchestrationError(
                f"Error running agent group {group}",
                cause=e,
                agent_group=group,
                suggestion="Check the agent configuration and ensure all agents are properly registered",
            )

    errors: List[Tuple[List[str], str]] = []
    results: List[Tuple[List[str], QueryResponse]] = []
    timeouts: List[List[str]] = []

    with tracer.start_as_current_span("parallel_query") as span:
        span.set_attribute("agent_groups", str(agent_groups))
        span.set_attribute("max_workers", max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(run_group, grp): grp for grp in agent_groups}
            import concurrent.futures

            try:
                for future in concurrent.futures.as_completed(futures, timeout=timeout):
                    grp = futures[future]
                    try:
                        result = future.result()
                        results.append((grp, result))
                        log.info(f"Agent group {grp} completed successfully")
                        span.add_event(f"Group {grp} completed")
                    except OrchestrationError as e:
                        errors.append((grp, str(e)))
                        log.error(f"Agent group {grp} failed: {e}", exc_info=True)
                        span.add_event(f"Group {grp} failed", {"error": str(e)})
            except concurrent.futures.TimeoutError:
                for fut, grp in futures.items():
                    if not fut.done():
                        fut.cancel()
                        timeouts.append(grp)
                        log.warning(f"Agent group {grp} timed out after {timeout} seconds")
                        span.add_event(f"Group {grp} timed out")

        execution_time = time.time() - start_time
        memory_usage_end = _get_memory_usage()
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
                "timeout_groups": len(timeouts),
            },
        )

    if not results and (errors or timeouts):
        details = []
        if errors:
            details.extend([f"{grp}: {err}" for grp, err in errors])
        if timeouts:
            details.extend([f"{grp}: timed out" for grp in timeouts])
        raise OrchestrationError(
            "All parallel agent groups failed or timed out",
            cause=None,
            errors=details,
            suggestion="Check the agent configurations and consider increasing the timeout.",
        )

    for group, result in results:
        confidence = _calculate_result_confidence(result)
        result_dict = {
            "claims": result.reasoning,
            "sources": result.citations,
            "metadata": {**result.metrics, "confidence": confidence, "agent_group": group},
            "results": {"group_answer": result.answer, "group_confidence": confidence},
        }
        final_state.update(result_dict)

    if errors or timeouts:
        err_info: Dict[str, Any] = {
            "claims": [],
            "metadata": {
                "errors": [f"{grp}: {err}" for grp, err in errors],
                "timeouts": [f"{grp}" for grp in timeouts],
            },
        }
        if errors:
            err_claims = [f"Error in agent group {grp}: {err}" for grp, err in errors]
            err_info["claims"].extend(err_claims)
        if timeouts:
            timeout_claims = [f"Agent group {grp} timed out" for grp in timeouts]
            err_info["claims"].extend(timeout_claims)
        final_state.update(err_info)

    synthesizer = AgentFactory.get("Synthesizer")
    aggregation_context = {
        "successful_groups": len(results),
        "error_groups": len(errors),
        "timeout_groups": len(timeouts),
        "execution_time": execution_time,
        "aggregation_strategy": "weighted_confidence",
    }
    final_state.update({"metadata": {"aggregation": aggregation_context}})

    final_result = synthesizer.execute(final_state, config)
    final_state.update(final_result)

    response = final_state.synthesize()
    if "answer" in final_result and final_result["answer"]:
        response.answer = final_result["answer"]

    response.metrics.update(
        {
            "parallel_execution": {
                "total_groups": len(agent_groups),
                "successful_groups": len(results),
                "error_groups": len(errors),
                "timeout_groups": len(timeouts),
                "execution_time": execution_time,
                "memory_delta_mb": memory_delta,
            }
        }
    )

    return response
