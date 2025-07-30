"""Circuit breaker utilities for agent orchestration."""
from __future__ import annotations

from typing import TypedDict
import time

from ..logging_utils import get_logger


class CircuitBreakerState(TypedDict):
    """State information for an agent's circuit breaker."""

    failure_count: float
    last_failure_time: float
    state: str
    recovery_attempts: int


# Global circuit breaker state for all agents
_circuit_breakers: dict[str, CircuitBreakerState] = {}

# Default configuration values; these are adjusted by the orchestrator
_circuit_breaker_threshold: int = 3
_circuit_breaker_cooldown: int = 30


def update_circuit_breaker(agent_name: str, error_category: str) -> None:
    """Update the circuit breaker state for an agent."""
    log = get_logger(__name__)

    if agent_name not in _circuit_breakers:
        _circuit_breakers[agent_name] = {
            "failure_count": 0.0,
            "last_failure_time": 0.0,
            "state": "closed",
            "recovery_attempts": 0,
        }

    breaker = _circuit_breakers[agent_name]
    current_time = time.time()

    if error_category in ["critical", "recoverable"]:
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = current_time
        if (
            breaker["failure_count"] >= _circuit_breaker_threshold
            and breaker["state"] == "closed"
        ):
            breaker["state"] = "open"
            log.warning(
                f"Circuit breaker for agent {agent_name} is now OPEN due to repeated failures",
                extra={"agent": agent_name, "circuit_state": "open", "failure_count": breaker["failure_count"]},
            )
    elif error_category == "transient":
        breaker["failure_count"] += 0.5
        breaker["last_failure_time"] = current_time

    if breaker["state"] == "open":
        cooling_period = _circuit_breaker_cooldown
        if current_time - breaker["last_failure_time"] > cooling_period:
            breaker["state"] = "half-open"
            breaker["recovery_attempts"] += 1
            log.info(
                f"Circuit breaker for agent {agent_name} is now HALF-OPEN, attempting recovery",
                extra={"agent": agent_name, "circuit_state": "half-open", "recovery_attempts": breaker["recovery_attempts"]},
            )


def handle_agent_success(agent_name: str) -> None:
    """Reset or downgrade the circuit breaker state on success."""
    breaker = _circuit_breakers.get(agent_name)
    if not breaker:
        return

    if breaker["state"] == "half-open":
        breaker["state"] = "closed"
        breaker["failure_count"] = 0.0
        breaker["last_failure_time"] = 0.0
        get_logger(__name__).info(
            f"Circuit breaker for agent {agent_name} CLOSED after successful recovery",
            extra={"agent": agent_name, "circuit_state": "closed"},
        )
    elif breaker["failure_count"] > 0:
        breaker["failure_count"] = max(0.0, breaker["failure_count"] - 1)


def get_circuit_breaker_state(agent_name: str) -> CircuitBreakerState:
    """Get the current circuit breaker state for an agent."""
    if agent_name not in _circuit_breakers:
        return {
            "state": "closed",
            "failure_count": 0.0,
            "last_failure_time": 0.0,
            "recovery_attempts": 0,
        }
    return _circuit_breakers[agent_name].copy()
