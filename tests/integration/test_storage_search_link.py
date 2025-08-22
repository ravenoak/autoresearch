import numpy as np
import pytest

from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch import storage


@pytest.fixture(autouse=True)
def setup_storage(tmp_path, monkeypatch):
    """Configure isolated in-memory storage and search for each test."""
    monkeypatch.chdir(tmp_path)
    ConfigLoader.reset_instance()

    cfg = ConfigModel()
    cfg.search.backends = []
    cfg.search.embedding_backends = ["duckdb"]
    cfg.search.context_aware.enabled = False
    cfg.storage.vector_extension = False
    cfg.storage.rdf_backend = "memory"
    cfg.storage.duckdb_path = str(tmp_path / "kg.duckdb")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    # Avoid ontology reasoning overhead during tests
    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner", lambda store, engine=None: None
    )

    storage.teardown(remove_db=True)
    StorageManager.setup(db_path=cfg.storage.duckdb_path)
    try:
        yield
    finally:
        storage.teardown(remove_db=True)
        ConfigLoader.reset_instance()


def _duckdb_backend_with_citations(query_embedding, max_results=5):
    conn = StorageManager.context.db_backend._conn
    rows = conn.execute("SELECT id, content FROM nodes WHERE content ILIKE '%python%'").fetchall()
    results = []
    for node_id, content in rows:
        citation_rows = conn.execute("SELECT dst FROM edges WHERE src = ?", [node_id]).fetchall()
        citations = [c[0] for c in citation_rows]
        results.append(
            {
                "title": content,
                "url": node_id,
                "snippet": content,
                "citations": citations,
            }
        )
    return results[:max_results]


@pytest.mark.slow
def test_external_lookup_returns_citations(monkeypatch):
    # Disable network backends and ranking complexity
    monkeypatch.setattr(Search, "backends", {})
    monkeypatch.setattr(
        Search,
        "cross_backend_rank",
        lambda q, b, query_embedding=None: sum(b.values(), []),
    )
    Search.embedding_backends["duckdb"] = _duckdb_backend_with_citations

    source = {
        "id": "https://python.org",
        "type": "source",
        "content": "Python official website",
    }
    StorageManager.persist_claim(source)

    claim = {
        "id": "c1",
        "type": "fact",
        "content": "Python is a programming language.",
        "embedding": [0.1, 0.2],
        "relations": [{"src": "c1", "dst": source["id"], "rel": "cites"}],
    }
    StorageManager.persist_claim(claim)
    monkeypatch.setattr(StorageManager, "persist_claim", lambda *a, **k: None)

    results = Search.external_lookup(
        {"text": "python", "embedding": np.array([0.1, 0.2])}, max_results=5
    )

    assert any(r["url"] == claim["id"] for r in results)
    retrieved = next(r for r in results if r["url"] == claim["id"])
    assert retrieved["citations"] == [source["id"]]
