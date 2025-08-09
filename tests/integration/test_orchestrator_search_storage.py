from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import orchestrator as orch_mod

Orchestrator = orch_mod.Orchestrator
AgentFactory = orch_mod.AgentFactory
StorageManager = orch_mod.StorageManager


class Search:
    @staticmethod
    def external_lookup(query, max_results=2):  # pragma: no cover - simple stub
        return []


def _make_agent(calls, stored):
    class SearchAgent:
        def __init__(self, name: str, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):  # pragma: no cover - dummy
            return True

        def execute(self, state, config, **kwargs):
            results = Search.external_lookup(state.query, max_results=2)
            for r in results:
                StorageManager.persist_claim(
                    {"id": r["url"], "type": "source", "content": r["title"]}
                )
            calls.append(self.name)
            state.results[self.name] = "ok"
            state.results["final_answer"] = "done"
            return {"results": {self.name: "ok"}}

    return SearchAgent("TestAgent")


def test_orchestrator_search_storage(monkeypatch):
    calls: list[str] = []
    stored: list[dict[str, str]] = []
    monkeypatch.setattr(
        Search,
        "external_lookup",
        lambda q, max_results=2: [
            {"title": "Doc1", "url": "u1"},
            {"title": "Doc2", "url": "u2"},
        ],
    )
    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim: stored.append(claim)
    )
    monkeypatch.setattr(AgentFactory, "get", lambda name: _make_agent(calls, stored))

    cfg = ConfigModel(agents=["TestAgent"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    resp = Orchestrator.run_query("q", cfg)
    assert isinstance(resp, QueryResponse)
    assert calls == ["TestAgent"]
    assert stored == [
        {"id": "u1", "type": "source", "content": "Doc1"},
        {"id": "u2", "type": "source", "content": "Doc2"},
    ]
    assert resp.answer == "done"
