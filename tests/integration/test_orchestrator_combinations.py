import itertools

import pytest

from types import SimpleNamespace
from contextlib import contextmanager

from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.models import QueryResponse


def make_agent(name, calls, search_calls, store_calls):
    class DummyAgent:
        def __init__(self, name, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):
            return True

        def execute(self, state, config, **kwargs):
            Search.rank_results("q", [{"title": "t", "url": "https://example.com"}])
            StorageManager.persist_claim({"id": self.name, "type": "fact", "content": self.name})
            calls.append(self.name)
            search_calls.append(self.name)
            state.update({"results": {self.name: "ok"}, "claims": [{"type": "fact", "content": self.name}]})
            if self.name == "Synthesizer":
                state.results["final_answer"] = f"Answer from {self.name}"
            return {"results": {self.name: "ok"}}

    return DummyAgent(name)


@pytest.mark.parametrize(
    "agents",
    list(itertools.permutations(["AgentA", "AgentB", "Synthesizer"])),
)
def test_orchestrator_agent_combinations(monkeypatch, agents):
    calls: list[str] = []
    search_calls: list[str] = []
    store_calls: list[str] = []
    monkeypatch.setattr(Search, "rank_results", lambda q, r: r)
    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim: store_calls.append(claim)
    )
    monkeypatch.setattr(
        AgentFactory,
        "get",
        lambda name, llm_adapter=None: make_agent(
            name, calls, search_calls, store_calls
        ),
    )

    @contextmanager
    def no_token_capture(agent_name, metrics, config):
        yield (lambda *a, **k: None, None)

    monkeypatch.setattr(
        Orchestrator, "_capture_token_usage", no_token_capture
    )

    cfg = SimpleNamespace(agents=list(agents), loops=1)
    response = Orchestrator.run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert calls == list(agents)
    assert search_calls == calls
    assert len(store_calls) == len(agents)
    assert response.answer == "Answer from Synthesizer"
