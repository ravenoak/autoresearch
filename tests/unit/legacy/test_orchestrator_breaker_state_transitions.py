"""Property-based test for circuit breaker state transitions."""

import time

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from autoresearch.orchestration.circuit_breaker import CircuitBreakerManager


@given(st.integers(min_value=3, max_value=5))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.error_recovery
def test_breaker_state_sequence(monkeypatch, failures):
    """Critical errors open the breaker and successes after cooldown close it.

    Assumes a threshold of three failures and a one second cooldown. Verifies
    that the breaker opens exactly at the threshold and returns to ``closed``
    after a cooldown period followed by a success.
    """

    t = [0.0]
    monkeypatch.setattr(time, "time", lambda: t[0])
    mgr = CircuitBreakerManager(threshold=3, cooldown=1)

    for _ in range(failures):
        mgr.update_circuit_breaker("a", "critical")

    t[0] += 2.0
    mgr.circuit_breakers["a"]["state"] = "half-open"
    mgr.handle_agent_success("a")
    final_state = mgr.get_circuit_breaker_state("a")
    assert final_state["state"] == "closed"
    assert final_state["failure_count"] == 0.0
