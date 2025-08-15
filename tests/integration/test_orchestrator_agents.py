import time
from typing import Dict, List
from unittest.mock import MagicMock

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.storage import StorageManager

# ---------------------------------------------------------------------------
# Helper factory for creating dummy agents
# ---------------------------------------------------------------------------


def make_agent(
    name: str, calls: List[str], seen_coalitions: Dict[str, Dict[str, List[str]]]
):
    class DummyAgent:
        def __init__(self, name: str, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):
            # Record coalitions visible to the agent for later assertions
            seen_coalitions[self.name] = dict(state.coalitions)
            return True

        def execute(self, state, config, **kwargs):
            calls.append(self.name)
            state.update(
                {
                    "claims": [f"claim {self.name}"],
                    "results": {self.name: "ok"},
                }
            )
            if self.name == "Synthesizer":
                # Synthesizer produces final answer based on accumulated claims
                final = ", ".join(calls)
                return {"answer": final, "results": {"final_answer": final}}
            return {"results": {self.name: "ok"}, "claims": [f"claim {self.name}"]}

    return DummyAgent(name)


# ---------------------------------------------------------------------------
# run_query: agent lists and coalitions
# ---------------------------------------------------------------------------


def test_run_query_with_coalitions(monkeypatch):
    calls: List[str] = []
    seen: Dict[str, Dict[str, List[str]]] = {}

    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: None)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        lambda name: make_agent(name, calls, seen),
    )

    cfg = ConfigModel(
        agents=["FactChecker", "Contrarian", "Synthesizer"],
        loops=1,
        coalitions={"Team": ["FactChecker", "Contrarian"]},
    )

    response = Orchestrator.run_query("q", cfg)

    assert response.answer == "FactChecker, Contrarian, Synthesizer"
    assert calls == ["FactChecker", "Contrarian", "Synthesizer"]
    assert "claim FactChecker" in response.reasoning
    assert "claim Contrarian" in response.reasoning
    assert seen["FactChecker"] == {"Team": ["FactChecker", "Contrarian"]}
    assert seen["Contrarian"] == {"Team": ["FactChecker", "Contrarian"]}


# ---------------------------------------------------------------------------
# run_parallel_query: aggregation of multiple groups
# ---------------------------------------------------------------------------


def test_run_parallel_query_aggregates_results(monkeypatch):
    cfg = ConfigModel(agents=[], loops=1)

    def mock_run_query(query, config):
        if config.agents == ["A"]:
            return QueryResponse(
                answer="a", citations=[], reasoning=["claim A"], metrics={}
            )
        return QueryResponse(
            answer="b", citations=[], reasoning=["claim B"], metrics={}
        )

    synthesizer = MagicMock()
    synthesizer.execute.return_value = {"answer": "final"}

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        lambda name: synthesizer,
    )

    resp = Orchestrator.run_parallel_query("q", cfg, [["A"], ["B"]])

    assert resp.answer == "final"
    assert "claim A" in resp.reasoning
    assert "claim B" in resp.reasoning
    assert resp.metrics["parallel_execution"]["total_groups"] == 2


# ---------------------------------------------------------------------------
# Failure cases: circuit breaker and timeout handling
# ---------------------------------------------------------------------------


def test_circuit_breaker_opens(monkeypatch):
    class FailingAgent:
        def can_execute(self, state, config):
            return True

        def execute(self, state, config, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: None)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        lambda name: FailingAgent() if name == "Bad" else make_agent(name, [], {}),
    )

    cfg = ConfigModel(
        agents=["Bad", "Synthesizer"], loops=1, circuit_breaker_threshold=1
    )

    orch = Orchestrator()
    with pytest.raises(Exception):
        orch.run_query("q", cfg)

    state = orch.get_circuit_breaker_state("Bad")
    assert state["state"] == "open"


def test_parallel_query_timeout(monkeypatch):
    cfg = ConfigModel(agents=[], loops=1)

    def slow_run_query(query, config):
        time.sleep(0.2)
        return QueryResponse(answer="slow", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", slow_run_query)

    with pytest.raises(Exception):
        Orchestrator.run_parallel_query("q", cfg, [["slow"]], timeout=0.05)
