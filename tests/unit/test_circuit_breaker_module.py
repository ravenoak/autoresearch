import types

from autoresearch.orchestration.circuit_breaker import CircuitBreakerManager


def test_state_transitions(monkeypatch):
    manager = CircuitBreakerManager()
    t = {"v": 0}
    monkeypatch.setattr(
        "autoresearch.orchestration.circuit_breaker.time",
        types.SimpleNamespace(time=lambda: t.setdefault("v", t["v"] + 10)),
    )
    for _ in range(3):
        manager.update_circuit_breaker("A", "recoverable")
    state = manager.get_circuit_breaker_state("A")
    assert state["state"] == "open"
    t["v"] += 40
    manager.circuit_breakers["A"]["last_failure_time"] = 0
    manager.update_circuit_breaker("A", "noop")
    state = manager.get_circuit_breaker_state("A")
    assert state["state"] == "half-open"


def test_recovery(monkeypatch):
    manager = CircuitBreakerManager()
    t = {"v": 0}
    monkeypatch.setattr(
        "autoresearch.orchestration.circuit_breaker.time",
        types.SimpleNamespace(time=lambda: t.setdefault("v", t["v"] + 10)),
    )
    for _ in range(3):
        manager.update_circuit_breaker("B", "recoverable")
    t["v"] += 40
    manager.circuit_breakers["B"]["last_failure_time"] = 0
    manager.update_circuit_breaker("B", "noop")
    manager.handle_agent_success("B")
    state = manager.get_circuit_breaker_state("B")
    assert state["state"] == "closed"
    assert state["failure_count"] == 0
