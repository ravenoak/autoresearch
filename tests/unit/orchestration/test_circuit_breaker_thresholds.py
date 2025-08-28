"""Simulate circuit breaker threshold and recovery.

Based on the proofs in `docs/algorithms/orchestration.md`.
"""

from __future__ import annotations

from autoresearch.orchestration.circuit_breaker import CircuitBreakerManager


def test_circuit_breaker_threshold_and_recovery() -> None:
    """Three critical failures open the breaker and recovery closes it."""

    times = [0.0]

    def fake_time() -> float:
        return times[0]

    mgr = CircuitBreakerManager(threshold=3, cooldown=1, time_func=fake_time)

    for _ in range(3):
        mgr.update_circuit_breaker("agent", "critical")
        times[0] += 0.1

    state = mgr.get_circuit_breaker_state("agent")
    assert state["state"] == "open"
    assert state["failure_count"] == 3

    times[0] += 1.1
    mgr.update_circuit_breaker("agent", "transient")
    state = mgr.get_circuit_breaker_state("agent")
    assert state["state"] == "half-open"

    mgr.handle_agent_success("agent")
    state = mgr.get_circuit_breaker_state("agent")
    assert state["state"] == "closed"
    assert state["failure_count"] == 0
