"""Utility helpers for orchestration components.

This module groups functions that were previously attached dynamically to
:class:`~autoresearch.orchestration.orchestrator.Orchestrator`. Keeping them in a
separate utility class makes the helpers easier to import directly in tests and
other modules without relying on dynamic attribute assignment.
"""

from __future__ import annotations

from .budgeting import _apply_adaptive_token_budget
from .error_handling import (
    _apply_recovery_strategy,
    _categorize_error,
    _handle_agent_error,
)
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
from .token_utils import _capture_token_usage, _execute_with_adapter
from .utils import calculate_result_confidence, get_memory_usage


class OrchestrationUtils:
    """Collection of static helpers used by the orchestrator."""

    # execution helpers
    get_agent = staticmethod(_get_agent)
    check_agent_can_execute = staticmethod(_check_agent_can_execute)
    deliver_messages = staticmethod(_deliver_messages)
    log_agent_execution = staticmethod(_log_agent_execution)
    call_agent_start_callback = staticmethod(_call_agent_start_callback)
    execute_agent_with_token_counting = staticmethod(_execute_agent_with_token_counting)
    handle_agent_completion = staticmethod(_handle_agent_completion)
    log_sources = staticmethod(_log_sources)
    persist_claims = staticmethod(_persist_claims)
    handle_agent_error = staticmethod(_handle_agent_error)

    # error handling helpers
    categorize_error = staticmethod(_categorize_error)
    apply_recovery_strategy = staticmethod(_apply_recovery_strategy)

    # core execution flows
    execute_agent = staticmethod(_execute_agent)
    execute_cycle = staticmethod(_execute_cycle)
    execute_cycle_async = staticmethod(_execute_cycle_async)
    rotate_list = staticmethod(_rotate_list)
    apply_adaptive_token_budget = staticmethod(_apply_adaptive_token_budget)

    # utility functions
    get_memory_usage = staticmethod(get_memory_usage)
    calculate_result_confidence = staticmethod(calculate_result_confidence)
    capture_token_usage = staticmethod(_capture_token_usage)
    execute_with_adapter = staticmethod(_execute_with_adapter)
