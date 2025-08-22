import itertools
from contextlib import contextmanager

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.models import QueryResponse


def make_agent(name, calls, store_calls):
    class DummyAgent:
        def __init__(self, name: str, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):  # pragma: no cover - dummy
            return True

        def execute(self, state, config, **kwargs):
            # Simulate search and storage interaction
            Search.rank_results("q", [{"title": "t", "url": "u"}])
            StorageManager.persist_claim({"id": name, "type": "fact", "content": name})
            calls.append(name)
            store_calls.append(name)
            state.results[name] = "ok"
            if name == "Synthesizer":
                state.results["final_answer"] = f"Answer from {name}"
            return {"results": {name: "ok"}}

    return DummyAgent(name)


pairs = list(itertools.permutations(["AgentA", "AgentB", "AgentC", "Synthesizer"], 2))


@pytest.mark.slow
@pytest.mark.parametrize("agents", pairs)
def test_orchestrator_all_agent_pairings(monkeypatch, agents):
    calls: list[str] = []
    stored: list[str] = []

    monkeypatch.setattr(Search, "rank_results", lambda q, r: r)
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim["id"]))
    monkeypatch.setattr(
        AgentFactory, "get", lambda name, llm_adapter=None: make_agent(name, calls, stored)
    )

    @contextmanager
    def no_token_capture(agent_name, metrics, config):
        yield (lambda *a, **k: None, None)

    monkeypatch.setattr(Orchestrator, "_capture_token_usage", no_token_capture)

    cfg = ConfigModel(agents=list(agents), loops=1)
    response = Orchestrator().run_query("q", cfg)

    assert isinstance(response, QueryResponse)
    assert calls == list(agents)
    assert stored == list(agents)
    expected = "Answer from Synthesizer" if "Synthesizer" in agents else "No answer synthesized"
    assert response.answer == expected
