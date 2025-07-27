from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.config import ConfigModel, ConfigLoader
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.models import QueryResponse


def _make_agent(calls, stored):
    class SearchAgent:
        def __init__(self, name: str, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):  # pragma: no cover - dummy
            return True

        def execute(self, state, config, **kwargs):
            results = Search.external_lookup(state.query, max_results=2)
            for r in results:
                StorageManager.persist_claim({"id": r["url"], "type": "source", "content": r["title"]})
                stored.append(r["url"])
            calls.append(self.name)
            state.results[self.name] = "ok"
            state.results["final_answer"] = "done"
            return {"results": {self.name: "ok"}}

    return SearchAgent("TestAgent")


def test_orchestrator_search_storage(monkeypatch):
    calls: list[str] = []
    stored: list[str] = []
    monkeypatch.setattr(Search, "external_lookup", lambda q, max_results=2: [
        {"title": "Doc1", "url": "u1"},
        {"title": "Doc2", "url": "u2"},
    ])
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim["id"]))
    monkeypatch.setattr(AgentFactory, "get", lambda name: _make_agent(calls, stored))

    cfg = ConfigModel(agents=["TestAgent"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    resp = Orchestrator.run_query("q", cfg)
    assert isinstance(resp, QueryResponse)
    assert calls == ["TestAgent"]
    assert stored == ["u1", "u2"]
    assert resp.answer == "done"
