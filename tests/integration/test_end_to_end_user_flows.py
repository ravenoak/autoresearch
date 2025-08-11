import pytest
from autoresearch.config.models import ConfigModel
from autoresearch.errors import OrchestrationError
from autoresearch.models import QueryResponse
from autoresearch.orchestration import orchestrator as orch_mod

Orchestrator = orch_mod.Orchestrator
AgentFactory = orch_mod.AgentFactory
StorageManager = orch_mod.StorageManager


class Search:
    @staticmethod
    def external_lookup(query, max_results=2):  # pragma: no cover - replaced in tests
        return []


def _make_success_agent(name, calls, stored):
    if name == "Searcher":
        class Searcher:
            def __init__(self, name, llm_adapter=None):
                self.name = name

            def can_execute(self, state, config):  # pragma: no cover - simple stub
                return True

            def execute(self, state, config, **kwargs):
                results = Search.external_lookup(state.query, max_results=2)
                state.results["search_results"] = results
                for r in results:
                    StorageManager.persist_claim(
                        {"id": r["url"], "type": "source", "content": r["title"]}
                    )
                calls.append(self.name)
                return {"results": {self.name: "ok"}}

        return Searcher(name)

    class Synthesizer:
        def __init__(self, name, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):  # pragma: no cover - simple stub
            return True

        def execute(self, state, config, **kwargs):
            docs = state.results.get("search_results", [])
            answer = ", ".join(d["title"] for d in docs)
            state.results["final_answer"] = f"Synthesized: {answer}"
            calls.append(self.name)
            return {"results": {self.name: answer}}

    return Synthesizer(name)


def _make_failing_agent(name, calls):
    class Searcher:
        def __init__(self, name, llm_adapter=None):
            self.name = name

        def can_execute(self, state, config):  # pragma: no cover - simple stub
            return True

        def execute(self, state, config, **kwargs):
            calls.append(self.name)
            # This will raise a RuntimeError from the patched lookup
            Search.external_lookup(state.query, max_results=2)
            return {"results": {self.name: "ok"}}

    return Searcher(name)


def test_end_to_end_successful_flow(monkeypatch):
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
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim))
    monkeypatch.setattr(AgentFactory, "get", lambda name: _make_success_agent(name, calls, stored))

    cfg = ConfigModel(agents=["Searcher", "Synthesizer"], loops=1)

    resp = Orchestrator.run_query("q", cfg)

    assert isinstance(resp, QueryResponse)
    assert calls == ["Searcher", "Synthesizer"]
    assert stored == [
        {"id": "u1", "type": "source", "content": "Doc1"},
        {"id": "u2", "type": "source", "content": "Doc2"},
    ]
    assert resp.answer == "Synthesized: Doc1, Doc2"


def test_end_to_end_search_failure(monkeypatch):
    calls: list[str] = []
    stored: list[dict[str, str]] = []

    def failing_lookup(query, max_results=2):
        raise RuntimeError("search failed")

    monkeypatch.setattr(Search, "external_lookup", failing_lookup)
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim))
    monkeypatch.setattr(AgentFactory, "get", lambda name: _make_failing_agent(name, calls))

    cfg = ConfigModel(agents=["Searcher"], loops=1, max_errors=1)

    with pytest.raises(OrchestrationError) as exc:
        Orchestrator.run_query("q", cfg)

    assert calls == ["Searcher"]
    assert stored == []
    errors = exc.value.context.get("errors", [])
    assert errors and errors[0]["agent"] == "Searcher"
    assert errors[0]["error_type"] == "RuntimeError"
