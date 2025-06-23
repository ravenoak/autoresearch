from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.config import ConfigModel, ConfigLoader
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
            store_calls.append(self.name)
            state.update({"results": {self.name: "ok"}, "claims": [{"type": "fact", "content": self.name}]})
            if self.name == "Synthesizer":
                state.results["final_answer"] = f"Answer from {self.name}"
            return {"results": {self.name: "ok"}}

    return DummyAgent(name)


def test_orchestrator_agent_combinations(monkeypatch):
    calls = []
    search_calls = []
    store_calls = []
    monkeypatch.setattr(Search, "rank_results", lambda q, r: r)
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: store_calls.append(claim))
    monkeypatch.setattr(AgentFactory, "get", lambda name: make_agent(name, calls, search_calls, store_calls))

    cfg = ConfigModel(agents=["AgentA", "Synthesizer"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    response = Orchestrator.run_query("q", cfg)
    assert isinstance(response, QueryResponse)
    assert calls == ["AgentA", "Synthesizer"]
    assert search_calls == calls
    assert len(store_calls) == 2
    assert response.answer == "Answer from Synthesizer"
