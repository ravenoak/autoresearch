import types
from autoresearch.orchestration import circuit_breaker


def test_state_transitions(monkeypatch):
    circuit_breaker._circuit_breakers.clear()
    t = {"v": 0}
    monkeypatch.setattr(
        "autoresearch.orchestration.circuit_breaker.time",
        types.SimpleNamespace(time=lambda: t.setdefault("v", t["v"] + 10)),
    )
    for _ in range(3):
        circuit_breaker.update_circuit_breaker("A", "recoverable")
    state = circuit_breaker.get_circuit_breaker_state("A")
    assert state["state"] == "open"
    t["v"] += 40
    circuit_breaker._circuit_breakers["A"]["last_failure_time"] = 0
    circuit_breaker.update_circuit_breaker("A", "noop")
    state = circuit_breaker.get_circuit_breaker_state("A")
    assert state["state"] == "half-open"


def test_recovery(monkeypatch):
    circuit_breaker._circuit_breakers.clear()
    t = {"v": 0}
    monkeypatch.setattr(
        "autoresearch.orchestration.circuit_breaker.time",
        types.SimpleNamespace(time=lambda: t.setdefault("v", t["v"] + 10)),
    )
    for _ in range(3):
        circuit_breaker.update_circuit_breaker("B", "recoverable")
    t["v"] += 40
    circuit_breaker._circuit_breakers["B"]["last_failure_time"] = 0
    circuit_breaker.update_circuit_breaker("B", "noop")
    circuit_breaker.handle_agent_success("B")
    state = circuit_breaker.get_circuit_breaker_state("B")
    assert state["state"] == "closed"
    assert state["failure_count"] == 0
