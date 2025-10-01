from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import orchestrator as orch_mod
from autoresearch.storage import ClaimAuditStatus

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
    def _capture_claim(claim: dict[str, object]) -> None:
        stored.append({key: str(claim[key]) for key in ("id", "type", "content")})

    monkeypatch.setattr(StorageManager, "persist_claim", _capture_claim)
    monkeypatch.setattr(AgentFactory, "get", lambda name: _make_agent(calls, stored))

    cfg = ConfigModel(agents=["TestAgent"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    resp = Orchestrator().run_query("q", cfg)
    assert isinstance(resp, QueryResponse)
    assert calls == ["TestAgent"]
    assert stored == [
        {"id": "u1", "type": "source", "content": "Doc1"},
        {"id": "u2", "type": "source", "content": "Doc2"},
    ]
    assert resp.answer == "done"


def test_orchestrator_multiple_agents_aggregate_results(monkeypatch):
    """Search results from one agent are aggregated and synthesized."""

    calls: list[str] = []
    stored: list[dict[str, str]] = []

    def _external_lookup(_: object, max_results: int = 2) -> list[dict[str, str]]:
        docs = [
            {"title": "Doc1", "url": "u1"},
            {"title": "Doc2", "url": "u2"},
        ]
        return docs[:max_results]

    def _capture_claim(claim: dict[str, object]) -> None:
        stored.append({key: str(claim[key]) for key in ("id", "type", "content")})

    monkeypatch.setattr(Search, "external_lookup", _external_lookup)
    monkeypatch.setattr(StorageManager, "persist_claim", _capture_claim)

    def make_agent(name: str):
        class Searcher:
            def __init__(self, name: str, llm_adapter=None):
                self.name = name

            def can_execute(self, state, config):  # pragma: no cover - dummy
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

        class Synthesizer:
            def __init__(self, name: str, llm_adapter=None):
                self.name = name

            def can_execute(self, state, config):  # pragma: no cover - dummy
                return True

            def execute(self, state, config, **kwargs):
                docs = state.results.get("search_results", [])
                answer = ", ".join(d["title"] for d in docs)
                calls.append(self.name)
                state.results["final_answer"] = f"Synthesized: {answer}"
                return {"results": {self.name: answer}}

        return Searcher(name) if name == "Searcher" else Synthesizer(name)

    monkeypatch.setattr(AgentFactory, "get", make_agent)

    cfg = ConfigModel(agents=["Searcher", "Synthesizer"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    resp = Orchestrator().run_query("q", cfg)
    assert isinstance(resp, QueryResponse)
    assert calls == ["Searcher", "Synthesizer"]
    assert stored == [
        {"id": "u1", "type": "source", "content": "Doc1"},
        {"id": "u2", "type": "source", "content": "Doc2"},
    ]
    assert "Synthesized: Doc1, Doc2" in resp.answer


def test_orchestrator_persists_across_queries(monkeypatch):
    """Claims from multiple queries are persisted."""

    calls: list[str] = []
    stored: list[dict[str, str]] = []

    monkeypatch.setattr(
        Search,
        "external_lookup",
        lambda q, max_results=2: [
            {"title": f"{q}-Doc1", "url": f"{q}-u1"},
            {"title": f"{q}-Doc2", "url": f"{q}-u2"},
        ],
    )
    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim: stored.append(claim)
    )
    monkeypatch.setattr(AgentFactory, "get", lambda name: _make_agent(calls, stored))

    cfg = ConfigModel(agents=["TestAgent"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    resp1 = Orchestrator().run_query("q1", cfg)
    resp2 = Orchestrator().run_query("q2", cfg)

    assert isinstance(resp1, QueryResponse)
    assert isinstance(resp2, QueryResponse)
    assert calls == ["TestAgent", "TestAgent"]
    assert stored == [
        {"id": "q1-u1", "type": "source", "content": "q1-Doc1"},
        {"id": "q1-u2", "type": "source", "content": "q1-Doc2"},
        {"id": "q2-u1", "type": "source", "content": "q2-Doc1"},
        {"id": "q2-u2", "type": "source", "content": "q2-Doc2"},
    ]
    assert resp1.answer == resp2.answer == "done"


def test_orchestrator_uses_config_context(config_context, monkeypatch):
    """Run orchestrator using the shared config fixture and persist claims."""

    calls: list[str] = []
    stored: list[dict[str, str]] = []

    def _external_lookup_context(_: object, max_results: int = 2) -> list[dict[str, str]]:
        docs = [
            {"title": "Doc1", "url": "u1"},
            {"title": "Doc2", "url": "u2"},
        ]
        return docs[:max_results]

    def _capture_claim_context(claim: dict[str, object]) -> None:
        stored.append({key: str(claim[key]) for key in ("id", "type", "content")})

    def _list_claim_audits_stub(claim_id: str | None = None) -> list[dict[str, str]]:
        matching = (
            [entry for entry in stored if entry["id"] == claim_id]
            if claim_id
            else stored
        )
        return [
            {"claim_id": entry["id"], "status": ClaimAuditStatus.SUPPORTED.value}
            for entry in matching
        ]

    monkeypatch.setattr(Search, "external_lookup", _external_lookup_context)
    monkeypatch.setattr(StorageManager, "persist_claim", _capture_claim_context)
    monkeypatch.setattr(StorageManager, "list_claim_audits", _list_claim_audits_stub)

    def make_agent(name: str):
        class Searcher:
            def __init__(self, name: str, llm_adapter=None):
                self.name = name

            def can_execute(self, state, config):  # pragma: no cover - dummy
                return True

            def execute(self, state, config, **kwargs):
                results = Search.external_lookup(state.query, max_results=2)
                state.results["search_results"] = results
                claims = [
                    {
                        "id": r["url"],
                        "type": "source",
                        "content": r["title"],
                        "audit_status": ClaimAuditStatus.SUPPORTED.value,
                    }
                    for r in results
                ]
                calls.append(self.name)
                return {"results": {self.name: "ok"}, "claims": claims}

        class Synthesizer:
            def __init__(self, name: str, llm_adapter=None):
                self.name = name

            def can_execute(self, state, config):  # pragma: no cover - dummy
                return True

            def execute(self, state, config, **kwargs):
                docs = state.results.get("search_results", [])
                answer = ", ".join(d["title"] for d in docs)
                calls.append(self.name)
                state.results["final_answer"] = f"Synthesized: {answer}"
                return {"results": {self.name: answer}}

        return Searcher(name) if name == "Searcher" else Synthesizer(name)

    monkeypatch.setattr(AgentFactory, "get", make_agent)

    cfg = config_context.config
    cfg.agents = ["Searcher", "Synthesizer"]
    cfg.loops = 1

    resp = Orchestrator().run_query("q", cfg)

    assert isinstance(resp, QueryResponse)
    assert calls == ["Searcher", "Synthesizer"]
    assert stored == [
        {"id": "u1", "type": "source", "content": "Doc1"},
        {"id": "u2", "type": "source", "content": "Doc2"},
    ]
    assert "Synthesized: Doc1, Doc2" in resp.answer


def test_orchestrator_handles_empty_search_results(monkeypatch):
    """Orchestrator stores nothing when search yields no results."""

    calls: list[str] = []
    stored: list[dict[str, str]] = []

    monkeypatch.setattr(Search, "external_lookup", lambda q, max_results=2: [])
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim))
    monkeypatch.setattr(AgentFactory, "get", lambda name: _make_agent(calls, stored))

    cfg = ConfigModel(agents=["TestAgent"], loops=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    resp = Orchestrator().run_query("q", cfg)

    assert isinstance(resp, QueryResponse)
    assert calls == ["TestAgent"]
    assert stored == []
    assert resp.answer == "done"
