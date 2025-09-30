from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator, Protocol, Sequence, cast

import networkx as nx
import numpy as np
import pytest
import rdflib
from numpy.typing import NDArray

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.search import Search
from autoresearch.search import storage as search_storage
from autoresearch.storage import StorageManager
from tests.conftest import VSS_AVAILABLE

if TYPE_CHECKING:  # pragma: no cover - typing helpers
    from autoresearch.cache import SearchCache
    from autoresearch.storage_backends import DuckDBStorageBackend
    from autoresearch.storage_typing import GraphProtocol

pytestmark = [
    pytest.mark.requires_vss,
    pytest.mark.skipif(not VSS_AVAILABLE, reason="VSS extension not available"),
]


Claim = dict[str, object]
VectorSearchResults = list[dict[str, object]]


class StorageBackendProtocol(Protocol):
    """Minimal protocol covering the backend methods used in these tests."""

    def persist_claim(self, claim: Claim) -> None:
        ...

    def update_claim(self, claim: Claim, partial_update: bool = False) -> None:
        ...

    def get_claim(self, claim_id: str) -> Claim:
        ...

    def has_vss(self) -> bool:
        ...

    def clear(self) -> None:
        ...


class DummyBackend(StorageBackendProtocol):
    """In-memory backend satisfying :class:`StorageManager` requirements."""

    def __init__(self) -> None:
        self._claims: dict[str, Claim] = {}

    def persist_claim(self, claim: Claim) -> None:
        claim_id = cast(str, claim.get("id", ""))
        self._claims[claim_id] = dict(claim)

    def update_claim(self, claim: Claim, partial_update: bool = False) -> None:
        claim_id = cast(str, claim.get("id", ""))
        existing = self._claims.setdefault(claim_id, {})
        if partial_update:
            existing.update(claim)
        else:
            self._claims[claim_id] = dict(claim)

    def get_claim(self, claim_id: str) -> Claim:
        return dict(self._claims.get(claim_id, {"id": claim_id}))

    def has_vss(self) -> bool:
        return False

    def clear(self) -> None:
        self._claims.clear()


class CacheProtocol(Protocol):
    """Protocol describing the subset of cache behaviour required for tests."""

    def get_cached_results(self, query: str, backend: str) -> VectorSearchResults | None:
        ...

    def cache_results(self, query: str, backend: str, results: VectorSearchResults) -> None:
        ...


@dataclass
class DummyCache(CacheProtocol):
    """Simple in-memory cache used to satisfy ``Search.cache`` typing."""

    _store: Dict[tuple[str, str], VectorSearchResults] = field(default_factory=dict)

    def get_cached_results(self, query: str, backend: str) -> VectorSearchResults | None:
        return self._store.get((query, backend))

    def cache_results(self, query: str, backend: str, results: VectorSearchResults) -> None:
        self._store[(query, backend)] = list(results)


@pytest.fixture(autouse=True)
def clean_storage(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Provide isolated in-memory storage for each test."""
    dummy_backend = DummyBackend()
    StorageManager.context.graph = nx.DiGraph()
    StorageManager.context.db_backend = cast("DuckDBStorageBackend", dummy_backend)
    StorageManager.context.rdf_store = cast("GraphProtocol", rdflib.Graph())
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)
    yield
    if StorageManager.context.graph is not None:
        StorageManager.context.graph.clear()
    if StorageManager.context.db_backend is not None:
        StorageManager.context.db_backend.clear()
    if StorageManager.context.rdf_store is not None:
        StorageManager.context.rdf_store.remove((None, None, None))


def _config_without_network() -> ConfigModel:
    cfg = ConfigModel()
    cfg.search.backends = []
    cfg.search.embedding_backends = ["duckdb"]
    cfg.search.context_aware.enabled = False
    return cfg


def test_search_returns_persisted_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _config_without_network()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    # Remove external backends and simplify ranking
    monkeypatch.setattr(Search, "backends", {})
    ns = Search()
    ns.backends = {}
    ns.cache = cast("SearchCache", DummyCache())
    monkeypatch.setattr(Search, "_shared_instance", ns)
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda self, q, b, query_embedding=None: sum(b.values(), []),
    )

    # Avoid index refresh for simplicity
    monkeypatch.setattr(StorageManager, "refresh_vector_index", lambda: None)
    monkeypatch.setattr(StorageManager, "touch_node", lambda _id: None)
    monkeypatch.setattr(StorageManager, "has_vss", lambda: False)

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
    search_storage.persist_claim(claim)
    assert calls, "run_ontology_reasoner should be invoked"

    def fake_vector_search(
        query_embedding: Sequence[float] | NDArray[np.floating[Any]],
        k: int = 5,
    ) -> VectorSearchResults:
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
        def get(self, *args: object, **kwargs: object) -> object:  # pragma: no cover
            raise AssertionError("network call not expected")

    monkeypatch.setattr(Search, "get_http_session", lambda: DummySession())

    results = Search.external_lookup(
        {"text": "", "embedding": np.array(claim["embedding"])}, max_results=1
    )
    assert results[0]["url"] == claim["id"]
    assert results[0]["snippet"] == claim["content"]


def test_storage_cleared_between_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _config_without_network()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(Search, "backends", {})
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda self, q, b, query_embedding=None: sum(b.values(), []),
    )

    def empty_vector_search(
        embedding: Sequence[float] | NDArray[np.floating[Any]],
        k: int = 5,
    ) -> VectorSearchResults:
        return []

    monkeypatch.setattr(StorageManager, "vector_search", empty_vector_search)

    class DummySession:
        def get(self, *args: object, **kwargs: object) -> object:  # pragma: no cover
            raise AssertionError("network call not expected")

    monkeypatch.setattr(Search, "get_http_session", lambda: DummySession())

    results = Search.external_lookup({"text": "", "embedding": np.array([0.2, 0.1])}, max_results=1)
    assert all(r["url"] != "c1" for r in results)


def test_external_lookup_persists_results(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _config_without_network()
    cfg.search.backends = ["b"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    stored: list[str] = []
    monkeypatch.setattr(search_storage, "persist_claim", lambda claim: stored.append(claim["id"]))

    def backend(query: str, max_results: int = 5) -> list[dict[str, object]]:
        return [{"title": "doc", "url": "u1"}]

    monkeypatch.setattr(Search, "backends", {"b": backend})
    ns = Search()
    ns.backends = {"b": backend}
    ns.cache = cast("SearchCache", DummyCache())
    monkeypatch.setattr(Search, "_shared_instance", ns)
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda self, q, b, query_embedding=None: sum(b.values(), []),
    )

    Search.external_lookup("q", max_results=1)
    assert stored == ["u1"], "search results should be persisted"


def test_search_reflects_updated_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _config_without_network()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    store: dict[str, Claim] = {
        "c1": {
            "id": "c1",
            "type": "fact",
            "content": "old",
            "embedding": [0.2, 0.1],
        }
    }

    monkeypatch.setattr(
        search_storage, "persist_claim", lambda claim: store.update({claim["id"]: claim})
    )
    monkeypatch.setattr(
        search_storage,
        "update_claim",
        lambda claim, partial_update=False: store[claim["id"]].update(claim),
        raising=False,
    )
    monkeypatch.setattr(Search, "backends", {})
    ns = Search()
    ns.backends = {}
    ns.cache = cast("SearchCache", DummyCache())
    monkeypatch.setattr(Search, "_shared_instance", ns)
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda self, q, b, query_embedding=None: sum(b.values(), []),
    )

    def vector_search(
        embedding: Sequence[float] | NDArray[np.floating[Any]],
        k: int = 5,
    ) -> VectorSearchResults:
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
    monkeypatch.setattr(StorageManager, "has_vss", lambda: False)

    search_storage.persist_claim(store["c1"])
    search_storage.update_claim({"id": "c1", "content": "new"}, partial_update=True)

    results = Search.external_lookup(
        {"text": "", "embedding": np.array(store["c1"]["embedding"])},
        max_results=1,
    )
    assert results[0]["snippet"] == "new", "search should reflect updated storage"


def test_search_persists_multiple_backend_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = _config_without_network()
    cfg.search.backends = ["b1", "b2"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    stored: list[str] = []
    monkeypatch.setattr(search_storage, "persist_claim", lambda claim: stored.append(claim["id"]))

    def b1(query: str, max_results: int = 5) -> list[dict[str, object]]:
        return [{"title": "Paris", "url": "u1"}]

    def b2(query: str, max_results: int = 5) -> list[dict[str, object]]:
        return [{"title": "France", "url": "u2"}]

    monkeypatch.setattr(Search, "backends", {"b1": b1, "b2": b2})
    ns = Search()
    ns.backends = {"b1": b1, "b2": b2}
    ns.cache = cast("SearchCache", DummyCache())
    monkeypatch.setattr(Search, "_shared_instance", ns)
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda self, q, b, query_embedding=None: sum(b.values(), []),
    )

    Search.external_lookup("What is the capital of France?", max_results=2)
    assert set(stored) == {"u1", "u2"}


def test_duckdb_persistence_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Claims persist across DuckDB sessions."""
    cfg = _config_without_network()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader.new_for_tests()
    import autoresearch.storage as storage_module
    storage_module._cached_config = None

    StorageManager.teardown(remove_db=True)
    StorageManager.setup(db_path=str(tmp_path / "kg.duckdb"))

    claim = {"id": "c1", "type": "fact", "content": "hello"}
    search_storage.persist_claim(claim)
    StorageManager.teardown()

    StorageManager.setup(db_path=str(tmp_path / "kg.duckdb"))
    retrieved = StorageManager.get_claim("c1")
    assert retrieved["content"] == "hello"
    StorageManager.teardown(remove_db=True)
    ConfigLoader.reset_instance()
