"""Deterministic simulation of circuit breaker states."""

from __future__ import annotations

from autoresearch.orchestration.circuit_breaker import simulate_circuit_breaker


def test_circuit_breaker_determinism_and_recovery() -> None:
    """Same event sequence always yields identical states and recovers."""

    events = [
        "critical",
        "critical",
        "critical",
        "tick",
        "tick",
        "recoverable",
        "success",
    ]

    states_first = simulate_circuit_breaker(events, threshold=3, cooldown=1)
    states_second = simulate_circuit_breaker(events, threshold=3, cooldown=1)

    assert states_first == states_second
    assert states_first[-1] == "closed"
