import itertools

import pytest

from autoresearch.agents.registry import AgentRegistry
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.models import QueryResponse
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.config.models import ConfigModel


@pytest.mark.parametrize("pair", list(itertools.combinations(AgentRegistry.list_available(), 2)))
def test_orchestrator_all_registered_pairs(monkeypatch, pair):
    """Run the orchestrator with every pair of registered agents."""

    # Setup
    calls: list[str] = []
    pair = list(pair)

    def make_agent(name: str):
        class DummyAgent:
            def __init__(self, name: str, llm_adapter=None) -> None:
                self.name = name

            def can_execute(self, state, config) -> bool:
                return True

            def execute(self, state, config, **_: object) -> dict:
                calls.append(name)
                state.results[name] = "ok"
                if name == pair[-1]:
                    state.results["final_answer"] = f"answer from {name}"
                return {"results": {name: "ok"}}

        return DummyAgent(name)

    monkeypatch.setattr(Search, "rank_results", lambda q, r: r)
    monkeypatch.setattr(StorageManager, "persist_claim", lambda c: None)
    monkeypatch.setattr(AgentFactory, "get", lambda name: make_agent(name))

    cfg = ConfigModel(agents=pair, loops=1)

    # Execute
    response = Orchestrator.run_query("q", cfg)

    # Verify
    assert isinstance(response, QueryResponse)
    assert calls == pair
    assert response.answer == f"answer from {pair[-1]}"
