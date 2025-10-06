from __future__ import annotations

from dataclasses import dataclass

from pytest import MonkeyPatch

from autoresearch.orchestration.circuit_breaker import (
    CircuitBreakerManager,
    CircuitBreakerState,
)


@dataclass
class IncrementingClock:
    """Deterministic clock used to simulate elapsed time in tests."""

    value: float = 0.0
    step: float = 10.0

    def time(self) -> float:
        self.value += self.step
        return self.value

    def advance(self, amount: float) -> None:
        self.value += amount


def test_state_transitions(monkeypatch: MonkeyPatch) -> None:
    manager = CircuitBreakerManager()
    clock = IncrementingClock()
    monkeypatch.setattr("autoresearch.orchestration.circuit_breaker.time", clock)
    for _ in range(3):
        manager.update_circuit_breaker("A", "recoverable")
    state: CircuitBreakerState = manager.get_circuit_breaker_state("A")
    assert state["state"] == "open"
    clock.advance(40)
    manager.circuit_breakers["A"]["last_failure_time"] = 0
    manager.update_circuit_breaker("A", "noop")
    state = manager.get_circuit_breaker_state("A")
    assert state["state"] == "half-open"


def test_recovery(monkeypatch: MonkeyPatch) -> None:
    manager = CircuitBreakerManager()
    clock = IncrementingClock()
    monkeypatch.setattr("autoresearch.orchestration.circuit_breaker.time", clock)
    for _ in range(3):
        manager.update_circuit_breaker("B", "recoverable")
    clock.advance(40)
    manager.circuit_breakers["B"]["last_failure_time"] = 0
    manager.update_circuit_breaker("B", "noop")
    manager.handle_agent_success("B")
    state = manager.get_circuit_breaker_state("B")
    assert state["state"] == "closed"
    assert state["failure_count"] == 0
