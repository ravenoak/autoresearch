"""Step definitions for circuit breaker recovery feature."""

from __future__ import annotations
from tests.behavior.utils import as_payload

from pytest_bdd import given, parsers, scenarios, then, when

from autoresearch.orchestration.circuit_breaker import CircuitBreakerManager


scenarios("../features/circuit_breaker_recovery.feature")


@given(
    parsers.parse("a circuit breaker with threshold {threshold:d} and cooldown {cooldown:d}"),
    target_fixture="breaker",
)
def breaker_fixture(threshold: int, cooldown: int) -> dict:
    """Create a circuit breaker manager with controllable time."""
    time_state = {"t": 0.0}

    def now() -> float:
        return time_state["t"]

    mgr = CircuitBreakerManager(threshold=threshold, cooldown=cooldown, time_func=now)
    return as_payload({"manager": mgr, "time": time_state})


@when("three critical failures occur")
def three_failures(breaker: dict) -> None:
    mgr = breaker["manager"]
    for _ in range(3):
        mgr.update_circuit_breaker("agent", "critical")


@when("a cooldown period elapses")
def cooldown_elapses(breaker: dict) -> None:
    breaker["time"]["t"] += breaker["manager"].cooldown + 0.1


@when("a success is recorded")
def success_recorded(breaker: dict) -> None:
    mgr = breaker["manager"]
    # Trigger half-open transition after cooldown
    mgr.update_circuit_breaker("agent", "transient")
    mgr.handle_agent_success("agent")


@then(parsers.parse('the breaker state should be "{state}"'))
def assert_state(breaker: dict, state: str) -> None:
    mgr = breaker["manager"]
    assert mgr.get_circuit_breaker_state("agent")["state"] == state


@then(parsers.parse("the failure count should be {count:d}"))
def assert_failure_count(breaker: dict, count: int) -> None:
    mgr = breaker["manager"]
    assert mgr.get_circuit_breaker_state("agent")["failure_count"] == float(count)
