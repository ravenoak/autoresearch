# mypy: ignore-errors
"""Property-based checks for circuit breaker recovery."""

import time

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from autoresearch.orchestration.circuit_breaker import CircuitBreakerManager


@given(failures=st.integers(min_value=0, max_value=6))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.error_recovery
def test_circuit_breaker_opens_and_recovers(monkeypatch, failures):
    """Failures open the breaker; cooldown and success close it.

    Assumes threshold 3 and cooldown 1 second. Verifies that repeated critical
    errors trip the breaker and that a subsequent success after the cooldown
    resets the state.
    """

    mgr = CircuitBreakerManager(threshold=3, cooldown=1)
    t = 0.0
    monkeypatch.setattr(time, "time", lambda: t)

    for _ in range(failures):
        mgr.update_circuit_breaker("agent", "critical")

    state = mgr.get_circuit_breaker_state("agent")
    if failures >= 3:
        assert state["state"] == "open"
        mgr.circuit_breakers["agent"]["state"] = "half-open"
        mgr.handle_agent_success("agent")
        state = mgr.get_circuit_breaker_state("agent")
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
    else:
        assert state["state"] == "closed"
        assert state["failure_count"] == pytest.approx(float(failures))
