"""Circuit breaker utilities for agent orchestration.

This module previously relied on module level globals to track circuit breaker
state and configuration. That made it difficult to isolate tests and reuse the
logic in different orchestration contexts. The new ``CircuitBreakerManager``
class encapsulates this state and exposes methods for updating and querying the
breaker for a given agent.
"""

from __future__ import annotations

import time
from typing import Callable, List, TypedDict

from ..logging_utils import get_logger


class CircuitBreakerState(TypedDict):
    """State information for an agent's circuit breaker."""

    failure_count: float
    last_failure_time: float
    state: str
    recovery_attempts: int


class CircuitBreakerManager:
    """Manage circuit breaker state for multiple agents."""

    def __init__(
        self,
        threshold: int = 3,
        cooldown: int = 30,
        *,
        time_func: Callable[[], float] | None = None,
    ) -> None:
        self.threshold = threshold
        self.cooldown = cooldown
        self.time_func = time_func or time.time
        self.circuit_breakers: dict[str, CircuitBreakerState] = {}

    # ------------------------------------------------------------------
    # State management helpers
    # ------------------------------------------------------------------
    def update_circuit_breaker(self, agent_name: str, error_category: str) -> None:
        """Update the circuit breaker state for ``agent_name``.

        ``error_category`` should be one of ``critical``, ``recoverable`` or
        ``transient``. Critical and recoverable errors increment the failure
        count by one while transient errors increment by 0.5.
        """

        log = get_logger(__name__)

        if agent_name not in self.circuit_breakers:
            self.circuit_breakers[agent_name] = {
                "failure_count": 0.0,
                "last_failure_time": 0.0,
                "state": "closed",
                "recovery_attempts": 0,
            }

        breaker = self.circuit_breakers[agent_name]
        current_time = self.time_func()
        elapsed = current_time - breaker["last_failure_time"]

        if error_category in ["critical", "recoverable"]:
            breaker["failure_count"] += 1
            breaker["last_failure_time"] = current_time
            if (
                breaker["failure_count"] >= self.threshold
                and breaker["state"] == "closed"
            ):
                breaker["state"] = "open"
                log.warning(
                    f"Circuit breaker for agent {agent_name} is now OPEN due to repeated failures",
                    extra={
                        "agent": agent_name,
                        "circuit_state": "open",
                        "failure_count": breaker["failure_count"],
                    },
                )
        elif error_category == "transient":
            breaker["failure_count"] += 0.5
            breaker["last_failure_time"] = current_time

        if breaker["state"] == "open" and elapsed > self.cooldown:
            breaker["state"] = "half-open"
            breaker["recovery_attempts"] += 1
            log.info(
                f"Circuit breaker for agent {agent_name} is now HALF-OPEN, attempting recovery",
                extra={
                    "agent": agent_name,
                    "circuit_state": "half-open",
                    "recovery_attempts": breaker["recovery_attempts"],
                },
            )

    def handle_agent_success(self, agent_name: str) -> None:
        """Reset or downgrade the circuit breaker state on success."""

        breaker = self.circuit_breakers.get(agent_name)
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

    def get_circuit_breaker_state(self, agent_name: str) -> CircuitBreakerState:
        """Return a copy of the current state for ``agent_name``."""

        if agent_name not in self.circuit_breakers:
            return {
                "state": "closed",
                "failure_count": 0.0,
                "last_failure_time": 0.0,
                "recovery_attempts": 0,
            }
        return self.circuit_breakers[agent_name].copy()


def simulate_circuit_breaker(
    events: List[str],
    *,
    threshold: int = 3,
    cooldown: int = 30,
) -> List[str]:
    """Simulate breaker states for a sequence of events.

    Args:
        events: Ordered list of ``"critical"``, ``"recoverable"``, ``"transient"``,
            ``"success"`` or ``"tick"`` events. ``"tick"`` advances time without
            modifying breaker state and is useful for simulating cooldown
            periods.
        threshold: Failure count before opening the breaker.
        cooldown: Steps to wait before half-open recovery.

    Returns:
        List of breaker states after each event.
    """

    time_steps = [0.0]

    def now() -> float:
        return time_steps[0]

    mgr = CircuitBreakerManager(
        threshold=threshold, cooldown=cooldown, time_func=now
    )
    states: List[str] = []

    for event in events:
        if event == "tick":
            states.append(mgr.get_circuit_breaker_state("agent")["state"])
            time_steps[0] += 1
            continue

        if event == "success":
            mgr.handle_agent_success("agent")
        else:
            mgr.update_circuit_breaker("agent", event)
        states.append(mgr.get_circuit_breaker_state("agent")["state"])
        time_steps[0] += 1

    return states


__all__ = [
    "CircuitBreakerManager",
    "CircuitBreakerState",
    "simulate_circuit_breaker",
]
