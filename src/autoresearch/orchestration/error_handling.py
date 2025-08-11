from __future__ import annotations

import time
import traceback
from typing import Dict

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


def _apply_recovery_strategy(
    agent_name: str, error_category: str, e: Exception, state: QueryState
) -> dict:
    """Apply an appropriate recovery strategy based on error category."""
    if error_category == "transient":
        recovery_strategy = "retry_with_backoff"
        suggestion = "This error is likely temporary. The system will automatically retry with backoff."
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
            extra={"agent": agent_name, "recovery_strategy": recovery_strategy},
        )
    elif error_category == "recoverable":
        recovery_strategy = "fallback_agent"
        suggestion = "This error indicates a configuration or input issue. A fallback approach will be used."
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
            extra={"agent": agent_name, "recovery_strategy": recovery_strategy},
        )
    else:
        recovery_strategy = "fail_gracefully"
        suggestion = "This is a critical error that requires attention. Check the logs for details."
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
            extra={"agent": agent_name, "recovery_strategy": recovery_strategy},
        )
    return {"recovery_strategy": recovery_strategy, "suggestion": suggestion}


def _handle_agent_error(
    agent_name: str, e: Exception, state: QueryState, metrics: OrchestrationMetrics
) -> Dict[str, object]:
    """Handle agent errors with granular recovery strategies."""
    error_category = _categorize_error(e)
    error_info: Dict[str, object] = {
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
    error_info.update(recovery_info)
    return error_info
