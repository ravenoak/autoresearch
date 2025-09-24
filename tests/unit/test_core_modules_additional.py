import types
from unittest.mock import MagicMock

import pytest

from autoresearch.agents.specialized.planner import PlannerAgent
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.orchestration.state import QueryState
from autoresearch.search import ExternalLookupResult, Search
from autoresearch.search.core import hybridmethod


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
    backend_calls: list[tuple[str, int, bool]] = []
    embedding_calls: list[str] = []
    add_calls: list[str] = []
    rank_calls: list[str] = []
    storage_calls: list[str] = []

    cfg = MagicMock()
    cfg.search.backends = ["stub"]
    cfg.search.embedding_backends = []
    cfg.search.context_aware.enabled = False
    cfg.search.max_workers = 1
    cfg.search.use_bm25 = True
    cfg.search.use_semantic_similarity = False
    cfg.search.use_source_credibility = False
    cfg.search.hybrid_query = False
    cfg.search.bm25_weight = 1.0
    cfg.search.semantic_similarity_weight = 0.0
    cfg.search.source_credibility_weight = 0.0
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr("autoresearch.search.core.get_cached_results", lambda q, n: None)
    monkeypatch.setattr("autoresearch.search.core.cache_results", lambda q, n, r: None)
    monkeypatch.setattr(Search, "calculate_bm25_scores", staticmethod(lambda q, r: [1.0]))
    monkeypatch.setattr("autoresearch.search.storage.persist_results", lambda results: None)

    shared = Search.get_instance()

    with shared.temporary_state() as search_instance:
        def _stub_backend(query: str, max_results: int = 5, *, return_handles: bool = False):
            backend_calls.append((query, max_results, return_handles))
            return [dict(result) for result in results]

        def _resolve_subject(subject):
            """Coerce hybridmethod callers to the shared instance for stable assertions."""

            # The descriptor mirrors production hybridmethod semantics by passing either
            # an instance or the class depending on how the stub is invoked; normalize both.
            return search_instance if subject is Search else subject

        def _stub_embedding(subject, query_embedding, max_results: int = 5):
            """Accept both instance and class callers to align with hybridmethod semantics."""

            target = _resolve_subject(subject)
            embedding_calls.append("instance" if target is search_instance else "other")
            return {}

        def _stub_add_embeddings(
            subject, documents, query_embedding=None
        ) -> None:  # pragma: no cover - trivial
            # The hybridmethod descriptor may send the class; normalize for backward compat.
            target = _resolve_subject(subject)
            add_calls.append("instance" if target is search_instance else "other")

        def _stub_rank_results(
            subject, query, result_docs, query_embedding=None
        ):  # pragma: no cover - trivial
            # Maintain compatibility with production methods that handle class or instance.
            target = _resolve_subject(subject)
            rank_calls.append("instance" if target is search_instance else "other")
            return result_docs

        def _stub_storage_lookup(
            subject, query, query_embedding, backend_results, max_results
        ):  # pragma: no cover - trivial
            # Storage lookups also need to support dual binding for hybridmethod parity.
            target = _resolve_subject(subject)
            storage_calls.append("instance" if target is search_instance else "other")
            return {}

        search_instance.backends = {"stub": _stub_backend}
        search_instance.embedding_backends = {}
        search_instance.cache.clear()
        monkeypatch.setattr(search_instance.cache, "get_cached_results", lambda *a, **k: None)
        monkeypatch.setattr(search_instance.cache, "cache_results", lambda *a, **k: None)

        monkeypatch.setattr(
            Search,
            "embedding_lookup",
            hybridmethod(_stub_embedding),
        )
        monkeypatch.setattr(
            Search,
            "add_embeddings",
            hybridmethod(_stub_add_embeddings),
        )
        monkeypatch.setattr(
            Search,
            "rank_results",
            hybridmethod(_stub_rank_results),
        )
        monkeypatch.setattr(
            Search,
            "storage_hybrid_lookup",
            hybridmethod(_stub_storage_lookup),
        )
        monkeypatch.setattr(
            Search,
            "get_instance",
            classmethod(lambda cls: search_instance),
        )

        instance_results = search_instance.external_lookup("q", max_results=1)
        assert [r["title"] for r in instance_results] == ["T"]
        assert [r["url"] for r in instance_results] == ["u"]

        bundle = Search.external_lookup("q", max_results=1, return_handles=True)
        assert isinstance(bundle, ExternalLookupResult)
        bundle_results = list(bundle)
        assert [r["title"] for r in bundle_results] == ["T"]
        assert [r["url"] for r in bundle_results] == ["u"]
        assert bundle.results == bundle_results
        assert bundle.cache is search_instance.cache

        instance_embedding = search_instance.embedding_lookup([0.1], 1)
        class_embedding = Search.embedding_lookup([0.1], 1)
        assert instance_embedding == {}
        assert class_embedding == {}

    assert backend_calls == [("q", 1, False), ("q", 1, False)]
    assert embedding_calls == ["instance", "instance"]
    assert add_calls[:2] == ["instance", "instance"]
    assert all(call == "instance" for call in rank_calls)
    assert len(rank_calls) >= 2
    assert all(call == "instance" for call in storage_calls)
    assert len(storage_calls) >= 2


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
    from autoresearch import storage

    if storage.KuzuBackend is None:
        pytest.skip("Kuzu backend not available")

    calls = {}

    class FakeDuck:
        def __init__(self):
            self.conn = object()

        def setup(self, path):
            calls["duck"] = path

        def get_connection(self):
            return self.conn

    class FakeGraph:
        def __init__(self, *a, **k):
            pass

        def open(self, *a, **k):
            pass

    cfg_storage = types.SimpleNamespace(
        use_kuzu=False,
        rdf_backend="memory",
        duckdb_path="db.duckdb",
        vector_extension=False,
        rdf_path="rdf_store",
    )
    cfg_model = types.SimpleNamespace(storage=cfg_storage)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg_model)
    ConfigLoader()._config = None
    monkeypatch.setattr("autoresearch.storage.DuckDBStorageBackend", lambda: FakeDuck())
    monkeypatch.setattr(
        "autoresearch.storage.rdflib", types.SimpleNamespace(Graph=lambda *a, **k: FakeGraph())
    )
    monkeypatch.setattr(
        "autoresearch.storage.KuzuBackend",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("Kuzu backend used")),
    )

    storage._cached_config = None
    storage.StorageManager.context.db_backend = None
    storage._kuzu_backend = None
    storage.setup("db")
    assert calls["duck"] == "db"
    storage.teardown()


def test_storage_setup_without_kuzu(monkeypatch):
    calls = {}

    class FakeDuck:
        def __init__(self):
            self.conn = object()

        def setup(self, path):  # noqa: D401 - trivial
            calls["duck"] = path

        def get_connection(self):  # noqa: D401 - trivial
            return self.conn

    class FakeGraph:
        def __init__(self, *a, **k):  # noqa: D401 - test stub
            pass

        def open(self, *a, **k):  # noqa: D401 - test stub
            pass

    cfg_storage = types.SimpleNamespace(
        use_kuzu=False,
        rdf_backend="memory",
        duckdb_path="db.duckdb",
        vector_extension=False,
        rdf_path="rdf_store",
    )
    cfg_model = types.SimpleNamespace(storage=cfg_storage)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg_model)
    ConfigLoader()._config = None
    monkeypatch.setattr("autoresearch.storage.DuckDBStorageBackend", lambda: FakeDuck())
    monkeypatch.setattr(
        "autoresearch.storage.rdflib", types.SimpleNamespace(Graph=lambda *a, **k: FakeGraph())
    )
    monkeypatch.setattr(
        "autoresearch.storage.KuzuBackend",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("Kuzu backend used")),
    )
    from autoresearch import storage

    storage._cached_config = None
    storage.StorageManager.context.db_backend = None
    storage._kuzu_backend = None
    storage.setup("db")
    assert calls["duck"] == "db"
    storage.teardown()
