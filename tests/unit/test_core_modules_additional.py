import types

from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.config.loader import ConfigLoader
from unittest.mock import MagicMock
from autoresearch.search import Search
from autoresearch.agents.specialized.planner import PlannerAgent
from autoresearch.orchestration.state import QueryState


def test_orchestrator_parse_config_basic():
    cfg = MagicMock()
    cfg.agents = ["A", "B"]
    cfg.loops = 2
    cfg.reasoning_mode = ReasoningMode.DIALECTICAL
    params = Orchestrator._parse_config(cfg)
    assert params["agents"] == ["A", "B"]
    assert params["loops"] == 2
    assert params["mode"] == ReasoningMode.DIALECTICAL
    assert params["agent_groups"] == [["A"], ["B"]]


def test_search_stub_backend(monkeypatch):
    results = [{"title": "T", "url": "u"}]

    @Search.register_backend("stub")
    def _stub(query: str, max_results: int = 5):
        return results

    cfg = MagicMock()
    cfg.search.backends = ["stub"]
    cfg.search.context_aware.enabled = False
    cfg.search.max_workers = 1
    cfg.search.use_bm25 = False
    cfg.search.use_semantic_similarity = False
    cfg.search.use_source_credibility = False
    cfg.search.bm25_weight = 1.0
    cfg.search.semantic_similarity_weight = 0.0
    cfg.search.source_credibility_weight = 0.0
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr(Search, "embedding_lookup", lambda emb, max_results=5: {})
    monkeypatch.setattr(Search, "add_embeddings", lambda res, emb: None)
    monkeypatch.setattr("autoresearch.search.core.get_cached_results", lambda q, n: None)
    monkeypatch.setattr("autoresearch.search.core.cache_results", lambda q, n, r: None)

    out = Search.external_lookup("q", max_results=1)
    assert out == results


def test_planner_execute(monkeypatch):
    agent = PlannerAgent()
    state = QueryState(query="test")
    cfg = MagicMock()

    class DummyAdapter:
        def generate(self, prompt: str, model: str | None = None) -> str:  # noqa: D401
            return "PLAN"

    monkeypatch.setattr(PlannerAgent, "get_adapter", lambda self, config: DummyAdapter())
    monkeypatch.setattr(PlannerAgent, "get_model", lambda self, config: "model")
    monkeypatch.setattr(PlannerAgent, "generate_prompt", lambda self, name, **kw: "prompt")

    result = agent.execute(state, cfg)
    assert result["results"]["research_plan"] == "PLAN"


def test_storage_setup_teardown(monkeypatch):
    calls = {}

    class FakeDuck:
        def __init__(self):
            self.conn = object()

        def setup(self, path):
            calls['duck'] = path

        def get_connection(self):
            return self.conn

    class FakeKuzu:
        def __init__(self):
            self.conn = object()

        def setup(self, path):
            calls['kuzu'] = path

        def get_connection(self):
            return self.conn

    class FakeGraph:
        def __init__(self, *a, **k):
            pass

        def open(self, *a, **k):
            pass
    cfg = MagicMock()
    cfg.storage.use_kuzu = True
    cfg.storage.kuzu_path = 'kuzu'
    cfg.storage.rdf_backend = 'memory'
    cfg.storage.duckdb_path = 'db.duckdb'
    cfg.storage.vector_extension = False
    monkeypatch.setattr(ConfigLoader, 'load_config', lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr('autoresearch.storage.DuckDBStorageBackend', lambda: FakeDuck())
    monkeypatch.setattr('autoresearch.storage.KuzuStorageBackend', lambda: FakeKuzu())
    monkeypatch.setattr('autoresearch.storage.rdflib', types.SimpleNamespace(Graph=lambda *a, **k: FakeGraph()))
    from autoresearch import storage
    storage.StorageManager.context.db_backend = None
    storage._kuzu_backend = None
    storage.setup('db')
    assert calls['duck'] == 'db'
    assert calls['kuzu'] == 'kuzu'
    storage.teardown()
