import types
from typing import Any
from unittest.mock import MagicMock

import pytest

from autoresearch.agents.specialized.planner import PlannerAgent
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.orchestration.state import QueryState
from autoresearch.search import ExternalLookupResult, Search
from autoresearch.search.core import hybridmethod
from autoresearch.storage import StorageManager


@pytest.fixture
def _stubbed_search_environment(monkeypatch, request):
    """Create a temporary Search instance with controllable backend stubs."""

    features: dict[str, Any] = getattr(request, "param", {}) or {}
    vector_search_enabled = bool(features.get("vector_search", False))

    backend_calls: list[tuple[str, int, bool]] = []
    embedding_calls: list[str] = []
    embedding_events: list[tuple[str, str]] = []
    compute_calls: list[tuple[str, str]] = []
    add_calls: list[str] = []
    rank_calls: list[str] = []
    storage_calls: list[str] = []
    cache_probes: list[dict[str, Any]] = []

    phase = "setup"

    def set_phase(label: str) -> None:
        nonlocal phase
        phase = label

    cfg = MagicMock()
    cfg.search.backends = ["stub"]
    cfg.search.embedding_backends = ["vector"] if vector_search_enabled else []
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
    monkeypatch.setattr("autoresearch.search.core.get_cached_results", lambda *a, **k: None)
    monkeypatch.setattr("autoresearch.search.core.cache_results", lambda *a, **k: None)
    monkeypatch.setattr(Search, "calculate_bm25_scores", staticmethod(lambda q, r: [1.0]))
    monkeypatch.setattr("autoresearch.search.storage.persist_results", lambda results: None)

    monkeypatch.setattr(
        StorageManager,
        "has_vss",
        staticmethod(lambda: vector_search_enabled),
    )

    shared = Search.get_instance()
    storage_payload: dict[str, list[dict]] = {}

    with shared.temporary_state() as search_instance:

        def _resolve_subject(subject):
            """Coerce hybridmethod callers to the shared instance for stable assertions."""

            return search_instance if subject is Search else subject

        def _stub_embedding(subject, query_embedding, max_results: int = 5):
            """Accept both instance and class callers to align with hybridmethod semantics."""

            target = _resolve_subject(subject)
            embedding_calls.append("instance" if target is search_instance else "other")
            embedding_events.append((phase, "instance" if target is search_instance else "other"))
            return {}

        def _stub_compute_embedding(subject, query: str):
            """Return a deterministic embedding when vector search extras are simulated."""

            target = _resolve_subject(subject)
            compute_calls.append((phase, "instance" if target is search_instance else "other"))
            if vector_search_enabled:
                return [0.42]
            return None

        def _stub_add_embeddings(subject, documents, query_embedding=None) -> None:
            """Maintain dual binding compatibility for add_embeddings."""

            target = _resolve_subject(subject)
            add_calls.append("instance" if target is search_instance else "other")

        def _stub_rank_results(subject, query, result_docs, query_embedding=None):
            """Track rank_results invocations while returning passthrough docs."""

            target = _resolve_subject(subject)
            rank_calls.append("instance" if target is search_instance else "other")
            return result_docs

        def _stub_storage_lookup(subject, query, query_embedding, backend_results, max_results):
            """Mirror storage lookup behaviour while allowing custom payloads."""

            target = _resolve_subject(subject)
            storage_calls.append("instance" if target is search_instance else "other")
            return {name: [dict(doc) for doc in docs] for name, docs in storage_payload.items()}

        search_instance.embedding_backends = {}
        search_instance.cache.clear()

        def _stub_cache_lookup(query: str, backend: str):
            cache_probes.append({})
            return None

        monkeypatch.setattr(search_instance.cache, "get_cached_results", _stub_cache_lookup)
        monkeypatch.setattr(search_instance.cache, "cache_results", lambda *a, **k: None)

        monkeypatch.setattr(Search, "embedding_lookup", hybridmethod(_stub_embedding))
        monkeypatch.setattr(
            Search,
            "compute_query_embedding",
            hybridmethod(_stub_compute_embedding),
        )
        monkeypatch.setattr(Search, "add_embeddings", hybridmethod(_stub_add_embeddings))
        monkeypatch.setattr(Search, "rank_results", hybridmethod(_stub_rank_results))
        monkeypatch.setattr(Search, "storage_hybrid_lookup", hybridmethod(_stub_storage_lookup))
        monkeypatch.setattr(Search, "get_instance", classmethod(lambda cls: search_instance))

        def install_backend(docs):
            if docs is None:
                search_instance.backends = {}
                cfg.search.backends = []
                return

            def _stub_backend(query: str, max_results: int = 5, *, return_handles: bool = False):
                backend_calls.append((query, max_results, return_handles))
                return [dict(result) for result in docs]

            search_instance.backends = {"stub": _stub_backend}
            cfg.search.backends = ["stub"]

        def set_storage_results(payload):
            storage_payload.clear()
            if payload:
                for name, docs in payload.items():
                    storage_payload[name] = [dict(doc) for doc in docs]

        install_backend([{"title": "T", "url": "u"}])

        environment = types.SimpleNamespace(
            cfg=cfg,
            search_instance=search_instance,
            backend_calls=backend_calls,
            embedding_calls=embedding_calls,
            embedding_events=embedding_events,
            compute_calls=compute_calls,
            add_calls=add_calls,
            rank_calls=rank_calls,
            storage_calls=storage_calls,
            cache_probes=cache_probes,
            set_phase=set_phase,
            vector_search_enabled=vector_search_enabled,
            install_backend=install_backend,
            set_storage_results=set_storage_results,
        )

        yield environment


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


@pytest.mark.parametrize(
    ("_stubbed_search_environment", "expected_embedding_calls"),
    [
        pytest.param({"vector_search": False}, {"search-instance": 0, "search-class": 0}, id="legacy"),
        pytest.param({"vector_search": True}, {"search-instance": 1, "search-class": 0}, id="vss-enabled"),
    ],
    indirect=["_stubbed_search_environment"],
)
def test_search_stub_backend(_stubbed_search_environment, expected_embedding_calls):
    """Exercise both legacy and vector-enabled lookup flows using the shared stub.

    The fixture accepts a feature dictionary so we can simulate environments where the
    DuckDB vector search extras are disabled (legacy) or enabled (vss-enabled). When the
    extras toggle is active, the stubbed ``compute_query_embedding`` emits a deterministic
    vector so ``Search.external_lookup`` performs additional embedding calls. We assert
    the dynamic counts rather than a fixed list to keep regression coverage across both
    pathways. Cache probes append empty dictionaries for each lookup to ensure miss
    semantics remain unchanged as the embedding behaviour varies.
    """

    docs = [{"title": "T", "url": "u"}]
    env = _stubbed_search_environment
    env.install_backend(docs)

    env.set_phase("search-instance")
    instance_results = env.search_instance.external_lookup("q", max_results=1)
    assert [r["title"] for r in instance_results] == ["T"]
    assert [r["url"] for r in instance_results] == ["u"]

    if env.vector_search_enabled:
        env.set_storage_results({"vector": []})

    env.set_phase("search-class")
    bundle = Search.external_lookup("q", max_results=1, return_handles=True)
    assert isinstance(bundle, ExternalLookupResult)
    bundle_results = list(bundle)
    assert [r["title"] for r in bundle_results] == ["T"]
    assert [r["url"] for r in bundle_results] == ["u"]
    assert bundle.results == bundle_results
    assert bundle.cache is env.search_instance.cache

    env.set_phase("direct")
    instance_embedding = env.search_instance.embedding_lookup([0.1], 1)
    class_embedding = Search.embedding_lookup([0.1], 1)
    assert instance_embedding == {}
    assert class_embedding == {}

    search_embedding_bindings = [
        binding
        for phase, binding in env.embedding_events
        if phase.startswith("search-")
    ]
    per_invocation_embeddings = {
        phase: [
            binding for event_phase, binding in env.embedding_events if event_phase == phase
        ]
        for phase in ("search-instance", "search-class")
    }
    direct_embedding_bindings = [
        binding
        for phase, binding in env.embedding_events
        if phase == "direct"
    ]

    total_expected_embeddings = sum(expected_embedding_calls.values())
    assert len(search_embedding_bindings) == total_expected_embeddings
    for phase, bindings in per_invocation_embeddings.items():
        assert len(bindings) == expected_embedding_calls[phase]
        assert all(binding == "instance" for binding in bindings)

    assert direct_embedding_bindings == ["instance", "instance"]

    compute_binding = [
        binding for phase, binding in env.compute_calls if phase.startswith("search-")
    ]
    expected_compute_calls = 0 if not env.vector_search_enabled else 2
    assert len(compute_binding) == expected_compute_calls
    assert all(binding == "instance" for binding in compute_binding)

    assert env.backend_calls == [("q", 1, False), ("q", 1, False)]
    assert env.add_calls[:2] == ["instance", "instance"]
    assert all(call == "instance" for call in env.rank_calls)
    assert len(env.rank_calls) >= 2
    assert all(call == "instance" for call in env.storage_calls)
    assert len(env.storage_calls) >= 2

    assert env.cache_probes
    assert all(hit == {} for hit in env.cache_probes)


def test_search_stub_backend_return_handles_fallback(_stubbed_search_environment):
    env = _stubbed_search_environment
    env.install_backend([])

    bundle = Search.external_lookup("missing", max_results=2, return_handles=True)

    assert isinstance(bundle, ExternalLookupResult)
    assert bundle.query == "missing"
    assert list(bundle) == bundle.results
    assert len(bundle.results) == 2
    assert all(result["title"].startswith("Result") for result in bundle.results)
    assert all(result["url"] == "" for result in bundle.results)
    assert bundle.cache is env.search_instance.cache
    assert bundle.by_backend == {}
    assert env.backend_calls == [("missing", 2, False)]


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
    graph = result["results"].get("task_graph")
    assert graph is not None
    assert graph["tasks"][0]["question"].startswith("PLAN")


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
