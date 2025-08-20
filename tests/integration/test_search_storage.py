import types

import networkx as nx
import pytest
import rdflib
import numpy as np

from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from tests.conftest import VSS_AVAILABLE

pytestmark = [
    pytest.mark.requires_vss,
    pytest.mark.skipif(not VSS_AVAILABLE, reason="VSS extension not available"),
]


@pytest.fixture(autouse=True)
def clean_storage(monkeypatch):
    """Provide isolated in-memory storage for each test."""
    dummy_backend = types.SimpleNamespace(
        persist_claim=lambda claim: None,
        update_claim=lambda claim, partial_update=False: None,
        clear=lambda: None,
    )
    StorageManager.context.graph = nx.DiGraph()
    StorageManager.context.db_backend = dummy_backend
    StorageManager.context.rdf_store = rdflib.Graph()
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)
    yield
    StorageManager.context.graph.clear()
    StorageManager.context.db_backend.clear()
    StorageManager.context.rdf_store.remove((None, None, None))


def _config_without_network() -> ConfigModel:
    cfg = ConfigModel()
    cfg.search.backends = []
    cfg.search.embedding_backends = ["duckdb"]
    cfg.search.context_aware.enabled = False
    return cfg


def test_search_returns_persisted_claim(monkeypatch):
    cfg = _config_without_network()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    # Remove external backends and simplify ranking
    monkeypatch.setattr(Search, "backends", {})
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda q, b, query_embedding=None: sum(b.values(), []),
    )

    # Avoid index refresh for simplicity
    monkeypatch.setattr(StorageManager, "refresh_vector_index", lambda: None)
    monkeypatch.setattr(StorageManager, "touch_node", lambda _id: None)

    # Track ontology reasoning calls
    calls = []
    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner",
        lambda store, engine=None: calls.append(True),
    )

    claim = {
        "id": "c1",
        "type": "fact",
        "content": "hello",
        "embedding": [0.2, 0.1],
    }
    StorageManager.persist_claim(claim)
    assert calls, "run_ontology_reasoner should be invoked"

    def fake_vector_search(query_embedding, k=5):
        return [
            {
                "node_id": claim["id"],
                "content": claim["content"],
                "embedding": claim["embedding"],
                "similarity": 1.0,
            }
        ]

    monkeypatch.setattr(StorageManager, "vector_search", fake_vector_search)

    class DummySession:
        def get(self, *a, **kw):  # pragma: no cover - network should not be used
            raise AssertionError("network call not expected")

    monkeypatch.setattr(Search, "get_http_session", lambda: DummySession())

    results = Search.external_lookup(
        {"text": "", "embedding": np.array(claim["embedding"])}, max_results=1
    )
    assert results[0]["url"] == claim["id"]
    assert results[0]["snippet"] == claim["content"]


def test_storage_cleared_between_tests(monkeypatch):
    cfg = _config_without_network()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(Search, "backends", {})
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda q, b, query_embedding=None: sum(b.values(), []),
    )
    monkeypatch.setattr(StorageManager, "vector_search", lambda e, k=5: [])

    class DummySession:
        def get(self, *a, **kw):  # pragma: no cover - network should not be used
            raise AssertionError("network call not expected")

    monkeypatch.setattr(Search, "get_http_session", lambda: DummySession())

    results = Search.external_lookup({"text": "", "embedding": np.array([0.2, 0.1])}, max_results=1)
    assert all(r["url"] != "c1" for r in results)


def test_external_lookup_persists_results(monkeypatch):
    cfg = _config_without_network()
    cfg.search.backends = ["b"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    stored: list[str] = []
    monkeypatch.setattr(StorageManager, "persist_claim", lambda claim: stored.append(claim["id"]))

    def backend(query: str, max_results: int = 5):
        return [{"title": "doc", "url": "u1"}]

    monkeypatch.setattr(Search, "backends", {"b": backend})
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda q, b, query_embedding=None: sum(b.values(), []),
    )

    Search.external_lookup("q", max_results=1)
    assert stored == ["u1"], "search results should be persisted"


def test_search_reflects_updated_claim(monkeypatch):
    cfg = _config_without_network()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    store: dict[str, dict] = {
        "c1": {
            "id": "c1",
            "type": "fact",
            "content": "old",
            "embedding": [0.2, 0.1],
        }
    }

    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim: store.update({claim["id"]: claim})
    )
    monkeypatch.setattr(
        StorageManager,
        "update_claim",
        lambda claim, partial_update=False: store[claim["id"]].update(claim),
    )
    monkeypatch.setattr(Search, "backends", {})
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda q, b, query_embedding=None: sum(b.values(), []),
    )

    def vector_search(embedding, k=5):
        claim = store["c1"]
        return [
            {
                "node_id": claim["id"],
                "content": claim["content"],
                "embedding": claim["embedding"],
                "similarity": 1.0,
            }
        ]

    monkeypatch.setattr(StorageManager, "vector_search", vector_search)
    monkeypatch.setattr(StorageManager, "refresh_vector_index", lambda: None)

    StorageManager.persist_claim(store["c1"])
    StorageManager.update_claim({"id": "c1", "content": "new"}, partial_update=True)

    results = Search.external_lookup(
        {"text": "", "embedding": np.array(store["c1"]["embedding"])},
        max_results=1,
    )
    assert results[0]["snippet"] == "new", "search should reflect updated storage"
