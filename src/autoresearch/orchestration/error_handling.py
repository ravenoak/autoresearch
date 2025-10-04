from __future__ import annotations

import time
import traceback
from typing import Any, Dict, cast

from ..errors import AgentError, NotFoundError, OrchestrationError, TimeoutError
from ..logging_utils import get_logger
from .metrics import OrchestrationMetrics
from .state import QueryState

log = get_logger(__name__)


def _categorize_error(e: Exception) -> str:
    """Categorize an error for appropriate handling."""
    if isinstance(e, TimeoutError):
        return "transient"
    if isinstance(e, NotFoundError):
        return "recoverable"
    if isinstance(e, AgentError):
        error_str = str(e).lower()
        if any(term in error_str for term in ["retry", "temporary", "timeout", "rate limit"]):
            return "transient"
        if any(term in error_str for term in ["configuration", "invalid input", "format"]):
            return "recoverable"
        return "critical"
    if isinstance(e, OrchestrationError):
        return "critical"
    return "critical"


def _build_diagnostic_claim(
    *,
    agent_name: str,
    content: str,
    error: Exception,
    error_category: str,
    recovery_strategy: str,
    suggestion: str,
    event: str,
) -> Dict[str, Any]:
    """Return a structured diagnostic claim for error recovery."""

    return {
        "type": "diagnostic",
        "subtype": event,
        "content": content,
        "debug": {
            "agent": agent_name,
            "error": str(error),
            "error_type": type(error).__name__,
            "error_category": error_category,
            "recovery_strategy": recovery_strategy,
            "suggestion": suggestion,
        },
    }


def _apply_recovery_strategy(
    agent_name: str, error_category: str, e: Exception, state: QueryState
) -> Dict[str, Any]:
    """Apply an appropriate recovery strategy based on error category."""

    claim: Dict[str, Any]
    if error_category == "transient":
        recovery_strategy = "retry_with_backoff"
        suggestion = (
            "This error is likely temporary. The system will automatically retry with backoff."
        )
        claim = _build_diagnostic_claim(
            agent_name=agent_name,
            content=(
                f"Agent {agent_name} encountered a temporary error while executing. "
                "Automatic retry with backoff has been scheduled."
            ),
            error=e,
            error_category=error_category,
            recovery_strategy=recovery_strategy,
            suggestion=suggestion,
            event="transient_error",
        )
        fallback_result = {
            "claims": [claim],
            "results": {
                "fallback": (
                    f"The {agent_name} agent encountered a temporary issue. "
                    "This is likely due to external factors and may resolve on retry."
                )
            },
            "metadata": {
                "recovery_applied": True,
                "recovery_strategy": recovery_strategy,
                "recovery_suggestion": suggestion,
            },
        }
        state.update(fallback_result)
        log.info(
            f"Applied '{recovery_strategy}' recovery strategy for agent {agent_name}",
            extra={"agent": agent_name, "recovery_strategy": recovery_strategy},
        )
    elif error_category == "recoverable":
        recovery_strategy = "fallback_agent"
        suggestion = (
            "This error indicates a configuration or input issue. A fallback approach will be used."
        )
        claim = _build_diagnostic_claim(
            agent_name=agent_name,
            content=(
                f"Agent {agent_name} encountered a recoverable error and "
                "a fallback agent path is being used."
            ),
            error=e,
            error_category=error_category,
            recovery_strategy=recovery_strategy,
            suggestion=suggestion,
            event="recoverable_error",
        )
        fallback_result = {
            "claims": [claim],
            "results": {
                "fallback": (
                    f"The {agent_name} agent encountered an issue that prevented it from completing normally. "
                    "A simplified approach has been used instead."
                )
            },
            "metadata": {
                "recovery_applied": True,
                "recovery_strategy": recovery_strategy,
                "recovery_suggestion": suggestion,
            },
        }
        state.update(fallback_result)
        log.info(
            f"Applied '{recovery_strategy}' recovery strategy for agent {agent_name}",
            extra={"agent": agent_name, "recovery_strategy": recovery_strategy},
        )
    else:
        recovery_strategy = "fail_gracefully"
        suggestion = "This is a critical error that requires attention. Check the logs for details."
        claim = _build_diagnostic_claim(
            agent_name=agent_name,
            content=(
                f"Agent {agent_name} encountered a critical error and failed gracefully. "
                "Manual intervention may be required."
            ),
            error=e,
            error_category=error_category,
            recovery_strategy=recovery_strategy,
            suggestion=suggestion,
            event="critical_error",
        )
        error_result = {
            "claims": [claim],
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
                "recovery_suggestion": suggestion,
            },
        }
        state.update(error_result)
        log.warning(
            f"Applied '{recovery_strategy}' recovery strategy for agent {agent_name}",
            extra={"agent": agent_name, "recovery_strategy": recovery_strategy},
        )
    return {
        "recovery_strategy": recovery_strategy,
        "suggestion": suggestion,
        "claim": claim,
    }


def _handle_agent_error(
    agent_name: str, e: Exception, state: QueryState, metrics: OrchestrationMetrics
) -> dict[str, object]:
    """Handle agent errors with granular recovery strategies."""
    error_category = _categorize_error(e)
    error_info: dict[str, object] = {
        "agent": agent_name,
        "error": str(e),
        "error_type": type(e).__name__,
        "error_category": error_category,
        "traceback": traceback.format_exc(),
        "timestamp": time.time(),
    }
    metrics.record_error(agent_name)
    if error_category == "critical":
        log.critical(
            f"Critical error during agent {agent_name} execution: {str(e)}",
            exc_info=True,
            extra={"error_info": error_info},
        )
    elif error_category == "recoverable":
        log.error(
            f"Recoverable error during agent {agent_name} execution: {str(e)}",
            exc_info=True,
            extra={"error_info": error_info},
        )
    else:
        log.warning(
            f"Transient error during agent {agent_name} execution: {str(e)}",
            exc_info=True,
            extra={"error_info": error_info},
        )
    recovery_info = _apply_recovery_strategy(agent_name, error_category, e, state)
    claim_payload = recovery_info.pop("claim", None)
    error_info.update(recovery_info)
    telemetry: Dict[str, Any] = {
        "error_category": error_category,
        "recovery_strategy": recovery_info.get("recovery_strategy"),
    }
    if claim_payload is not None:
        claim_dict = cast(Dict[str, Any], claim_payload)
        error_info["claim"] = claim_dict
        telemetry["claim_debug"] = cast(Dict[str, Any], claim_dict.get("debug", {}))
    error_info["telemetry"] = telemetry
    return error_info
