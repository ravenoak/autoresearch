from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from _pytest.monkeypatch import MonkeyPatch
from numpy.typing import NDArray

from autoresearch import storage
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.storage_typing import DuckDBConnectionProtocol, JSONDict


@pytest.fixture(autouse=True)
def setup_storage(tmp_path: Path, monkeypatch: MonkeyPatch) -> Iterator[None]:
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

    def load_config_stub(_: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_stub)

    # Avoid ontology reasoning overhead during tests
    def noop_reasoner(*_: object, **__: object) -> None:
        return None

    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner", noop_reasoner
    )

    storage.teardown(remove_db=True)
    StorageManager.setup(db_path=cfg.storage.duckdb_path)
    try:
        yield
    finally:
        storage.teardown(remove_db=True)
        ConfigLoader.reset_instance()


def _duckdb_backend_with_citations(
    _query_embedding: NDArray[np.float64] | list[float], max_results: int = 5
) -> list[JSONDict]:
    db_backend = StorageManager.context.db_backend
    if db_backend is None:
        raise RuntimeError("DuckDB backend is not initialised")
    conn: DuckDBConnectionProtocol = db_backend.get_connection()
    rows = conn.execute(
        "SELECT id, content FROM nodes WHERE content ILIKE '%python%'"
    ).fetchall()
    results: list[JSONDict] = []
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
def test_external_lookup_returns_citations(monkeypatch: MonkeyPatch) -> None:
    # Disable network backends and ranking complexity
    monkeypatch.setattr(Search, "backends", {})

    def rank_all(
        _query: JSONDict,
        backends: dict[str, list[JSONDict]],
        query_embedding: NDArray[np.float64] | None = None,
    ) -> list[JSONDict]:
        return [item for results in backends.values() for item in results]

    monkeypatch.setattr(Search, "cross_backend_rank", rank_all)
    Search.embedding_backends["duckdb"] = _duckdb_backend_with_citations

    source: JSONDict = {
        "id": "https://python.org",
        "type": "source",
        "content": "Python official website",
    }
    StorageManager.persist_claim(source)

    claim: JSONDict = {
        "id": "c1",
        "type": "fact",
        "content": "Python is a programming language.",
        "embedding": [0.1, 0.2],
        "relations": [{"src": "c1", "dst": source["id"], "rel": "cites"}],
    }
    StorageManager.persist_claim(claim)

    def ignore_persist(*_: Any, **__: Any) -> None:
        return None

    monkeypatch.setattr(StorageManager, "persist_claim", ignore_persist)

    query: JSONDict = {"text": "python", "embedding": np.array([0.1, 0.2])}
    results = Search.external_lookup(query, max_results=5)

    assert any(r["url"] == claim["id"] for r in results)
    retrieved = next(r for r in results if r["url"] == claim["id"])
    assert retrieved["citations"] == [source["id"]]
