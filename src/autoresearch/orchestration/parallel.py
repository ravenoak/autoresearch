"""Parallel execution helpers for agent groups."""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from ..config.models import ConfigModel
from ..models import QueryResponse
from .state import QueryState
from ..agents.registry import AgentFactory
from ..errors import AgentError, OrchestrationError, TimeoutError
from ..logging_utils import get_logger
from ..tracing import get_tracer, setup_tracing
from .utils import (
    get_memory_usage as _get_memory_usage,
    calculate_result_confidence as _calculate_result_confidence,
)


log = get_logger(__name__)


def _diagnostic_claim_for_group(
    group: Sequence[str],
    *,
    message: str,
    event: str,
    detail: str,
    timeout: float | None = None,
) -> Dict[str, Any]:
    """Return a structured diagnostic claim for parallel execution issues."""

    debug_payload: Dict[str, Any] = {
        "agent_group": [str(agent) for agent in group],
        "event": event,
        "detail": detail,
    }
    if timeout is not None:
        debug_payload["timeout_seconds"] = timeout
    return {
        "type": "diagnostic",
        "subtype": f"parallel_group_{event}",
        "content": message,
        "debug": debug_payload,
    }


def execute_parallel_query(
    query: str,
    config: ConfigModel,
    agent_groups: Sequence[Sequence[str]],
    timeout: int = 300,
) -> QueryResponse:
    """Run multiple agent groups in parallel and synthesize results."""

    setup_tracing(getattr(config, "tracing_enabled", False))
    tracer = get_tracer(__name__)
    log = get_logger(__name__)

    final_state = QueryState(query=query, coalitions=getattr(config, "coalitions", {}))

    # Normalise the incoming groups so downstream logic can freely mutate or
    # index into them without mutating caller-owned containers such as tuples.
    group_list: List[List[str]] = [list(group) for group in agent_groups]

    cpu_count = os.cpu_count() or 4
    max_workers = min(len(group_list), max(1, cpu_count - 1))

    start_time = time.time()
    memory_usage_start = _get_memory_usage()

    total_agents = sum(len(g) for g in group_list)

    def run_group(group: List[str]) -> QueryResponse:
        from .orchestrator import Orchestrator

        group_payload = config.model_dump()
        group_payload.update(
            {
                "agents": list(group),
                "group_size": len(group),
                "total_groups": len(group_list),
                "total_agents": total_agents,
            }
        )
        group_payload.setdefault("token_budget", getattr(config, "token_budget", 4000))
        group_config = ConfigModel.model_validate(group_payload)

        try:
            return Orchestrator().run_query(query, group_config)
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
        span.set_attribute("agent_groups", str(group_list))
        span.set_attribute("max_workers", max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(run_group, grp): grp for grp in group_list}
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
        raw_claims = result.reasoning
        claims: list[dict[str, object]] = []
        if isinstance(raw_claims, Sequence) and not isinstance(raw_claims, (str, bytes)):
            for entry in raw_claims:
                if isinstance(entry, Mapping):
                    claims.append(dict(entry))
                else:
                    claims.append({"text": str(entry)})
        elif raw_claims is not None:
            claims.append({"text": str(raw_claims)})
        result_dict = {
            "claims": claims,
            "sources": result.citations,
            "metadata": {**result.metrics, "confidence": confidence, "agent_group": group},
            "results": {"group_answer": result.answer, "group_confidence": confidence},
        }
        final_state.update(result_dict)

    if errors or timeouts:
        err_claims: list[dict[str, object]] = []
        if errors:
            err_claims.extend(
                _diagnostic_claim_for_group(
                    grp,
                    message=f"Error in agent group {grp}: {err}",
                    event="error",
                    detail=str(err),
                )
                for grp, err in errors
            )
        if timeouts:
            err_claims.extend(
                _diagnostic_claim_for_group(
                    grp,
                    message=f"Agent group {grp} timed out",
                    event="timeout",
                    detail="timeout",
                    timeout=float(timeout),
                )
                for grp in timeouts
            )
        err_info: Dict[str, Any] = {
            "claims": err_claims,
            "metadata": {
                "errors": [f"{grp}: {err}" for grp, err in errors],
                "timeouts": [f"{grp}" for grp in timeouts],
            },
        }
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
                "total_groups": len(group_list),
                "successful_groups": len(results),
                "error_groups": len(errors),
                "timeout_groups": len(timeouts),
                "execution_time": execution_time,
                "memory_delta_mb": memory_delta,
            }
        }
    )

    return response
