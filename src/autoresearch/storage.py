"""Hybrid DKG persistence: NetworkX, DuckDB, RDFLib."""

from __future__ import annotations

import os
import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Optional, cast

import duckdb
import networkx as nx
import rdflib
from .config import ConfigLoader
from .logging_utils import get_logger
from .orchestration.metrics import EVICTION_COUNTER

# Global containers initialised in `setup`
_graph: Optional[nx.DiGraph[Any]] = None
_db_path: Optional[str] = None
_db_conn: Optional[duckdb.DuckDBPyConnection] = None
_rdf_store: Optional[rdflib.Graph] = None
_lock = Lock()
_lru: "OrderedDict[str, float]" = OrderedDict()
log = get_logger(__name__)

# Optional injection point for tests
_delegate: type["StorageManager"] | None = None


def set_delegate(delegate: type["StorageManager"] | None) -> None:
    """Replace StorageManager implementation globally."""
    global _delegate
    _delegate = delegate


def get_delegate() -> type["StorageManager"] | None:
    """Return the injected StorageManager class if any."""
    return _delegate


def setup(db_path: Optional[str] = None) -> None:
    """Initialise storage components if not already initialised."""
    global _graph, _db_path, _db_conn, _rdf_store
    with _lock:
        if _db_conn is not None:
            return

        _graph = nx.DiGraph()
        path: str = (
            db_path
            if db_path is not None
            else os.getenv("DUCKDB_PATH", "kg.duckdb")
        )
        _db_path = path
        _db_conn = duckdb.connect(path)

        cfg = ConfigLoader().config.storage
        store_name = (
            "Sleepycat" if cfg.rdf_backend == "berkeleydb" else "SQLite"
        )
        try:
            _rdf_store = rdflib.Graph(store=store_name)
            _rdf_store.open(cfg.rdf_path, create=True)
        except Exception as e:  # pragma: no cover - store may fail
            log.error(f"Failed to open RDF store: {e}")
            _rdf_store = rdflib.Graph()
        if cfg.vector_extension:
            try:
                _db_conn.execute("INSTALL vector")
                _db_conn.execute("LOAD vector")
            except Exception as e:  # pragma: no cover - extension may fail
                log.error(f"Failed to load vector extension: {e}")

        # Ensure required tables exist
        _db_conn.execute(
            "CREATE TABLE IF NOT EXISTS nodes("
            "id VARCHAR, type VARCHAR, content VARCHAR, "
            "conf DOUBLE, ts TIMESTAMP)"
        )
        _db_conn.execute(
            "CREATE TABLE IF NOT EXISTS edges("
            "src VARCHAR, dst VARCHAR, rel VARCHAR, "
            "w DOUBLE)"
        )
        _db_conn.execute(
            "CREATE TABLE IF NOT EXISTS embeddings("
            "node_id VARCHAR, embedding DOUBLE[])"
        )

        if cfg.vector_extension:
            StorageManager.create_hnsw_index()


def teardown(remove_db: bool = False) -> None:
    """Close connections and optionally remove the DuckDB file."""
    global _graph, _db_conn, _rdf_store
    with _lock:
        if _db_conn is not None:
            _db_conn.close()
        if _rdf_store is not None:
            try:
                _rdf_store.close()
            except Exception:  # pragma: no cover - optional close
                pass
        if remove_db and _db_path and os.path.exists(_db_path):
            os.remove(_db_path)
        cfg = ConfigLoader().config.storage
        if remove_db and os.path.exists(cfg.rdf_path):
            if os.path.isdir(cfg.rdf_path):
                import shutil

                shutil.rmtree(cfg.rdf_path, ignore_errors=True)
            else:
                os.remove(cfg.rdf_path)
        _graph = None
        _db_conn = None
        _rdf_store = None


class StorageManager:
    @staticmethod
    def setup(db_path: Optional[str] = None) -> None:
        """Initialise storage, delegating if a custom implementation is set."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.setup(db_path)
        setup(db_path)

    @staticmethod
    def _current_ram_mb() -> float:
        """Return approximate RAM usage of the current process in MB."""
        try:
            import psutil  # type: ignore[import-untyped]

            mem = psutil.Process(os.getpid()).memory_info().rss
            return float(mem) / (1024**2)
        except Exception:  # pragma: no cover - psutil may not be available
            try:
                import resource

                usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                # ru_maxrss is KB on Linux, bytes on macOS
                if usage > 1024**2:
                    return usage / (1024**2)
                return usage / 1024
            except Exception:
                return 0.0

    @staticmethod
    def _enforce_ram_budget(budget_mb: int) -> None:
        """Evict nodes when memory exceeds the configured budget."""
        if budget_mb <= 0:
            return

        policy = ConfigLoader().config.graph_eviction_policy

        def _pop_lru() -> str | None:
            if not _lru:
                return None
            node_id, _ = _lru.popitem(last=False)
            return node_id

        def _pop_low_score() -> str | None:
            if not _graph or not _graph.nodes:
                return None
            node_id = cast(
                str,
                min(
                    _graph.nodes,
                    key=lambda n: _graph.nodes[n].get("confidence", 0.0),
                ),
            )
            if node_id in _lru:
                del _lru[node_id]
            return node_id

        while _graph and StorageManager._current_ram_mb() > budget_mb:
            node_id: str | None
            if policy == "score":
                node_id = _pop_low_score()
            else:
                node_id = _pop_lru()
            if node_id is None:
                break
            if _graph.has_node(node_id):
                _graph.remove_node(node_id)
                EVICTION_COUNTER.inc()
                log.info(
                    "Evicted node %s due to RAM budget (policy=%s)",
                    node_id,
                    policy,
                )

    @staticmethod
    def persist_claim(claim: dict[str, Any]) -> None:
        """Persist claim, delegating if a custom implementation is set."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.persist_claim(claim)
        """Persist claim to NetworkX, DuckDB, and RDFLib."""
        with _lock:
            if _db_conn is None or _graph is None or _rdf_store is None:
                setup()
            assert _db_conn is not None
            assert _graph is not None
            assert _rdf_store is not None
            # NetworkX
            attrs = dict(claim.get("attributes", {}))
            if "confidence" in claim:
                attrs["confidence"] = claim["confidence"]
            _graph.add_node(claim["id"], **attrs)
            _lru[claim["id"]] = time.time()
            for rel in claim.get("relations", []):
                _graph.add_edge(
                    rel["src"],
                    rel["dst"],
                    **rel.get("attributes", {}),
                )
            # DuckDB
            # insert node row
            _db_conn.execute(
                "INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                [
                    claim["id"],
                    claim.get("type", ""),
                    claim.get("content", ""),
                    claim.get("confidence", 0.0),
                ],
            )
            # insert edges
            for rel in claim.get("relations", []):
                _db_conn.execute(
                    "INSERT INTO edges VALUES (?, ?, ?, ?)",
                    [
                        rel["src"],
                        rel["dst"],
                        rel.get("rel", ""),
                        rel.get("weight", 1.0),
                    ],
                )
            # insert embedding
            embedding = claim.get("embedding")
            if embedding is not None:
                _db_conn.execute(
                    "INSERT INTO embeddings VALUES (?, ?)",
                    [claim["id"], embedding],
                )
            # RDFLib quad persistence
            subj = rdflib.URIRef(f"urn:claim:{claim['id']}")
            for k, v in claim.get("attributes", {}).items():
                pred = rdflib.URIRef(f"urn:prop:{k}")
                obj = rdflib.Literal(v)
                _rdf_store.add((subj, pred, obj))

            # Check RAM usage and evict if needed
            budget = ConfigLoader().config.ram_budget_mb
            StorageManager._enforce_ram_budget(budget)

    @staticmethod
    def create_hnsw_index() -> None:
        """Create HNSW index on the embeddings table or delegate."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.create_hnsw_index()
        if _db_conn is None:
            setup()
        assert _db_conn is not None
        cfg = ConfigLoader().config.storage
        try:
            _db_conn.execute(
                "CREATE INDEX IF NOT EXISTS embeddings_hnsw "
                "ON embeddings USING hnsw (embedding) "
                f"WITH (m={cfg.hnsw_m}, "
                f"ef_construction={cfg.hnsw_ef_construction}, "
                f"metric='{cfg.hnsw_metric}')"
            )
        except Exception as e:  # pragma: no cover - index creation may fail
            log.error(f"Failed to create HNSW index: {e}")

    @staticmethod
    def vector_search(
        query_embedding: list[float], k: int = 5
    ) -> list[dict[str, Any]]:
        """Return nearest nodes by vector similarity or delegate."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.vector_search(query_embedding, k)
        conn = StorageManager.get_duckdb_conn()
        cfg = ConfigLoader().config
        try:
            try:
                conn.execute(f"SET hnsw_ef_search={cfg.vector_nprobe}")
            except Exception:
                pass
            vector_literal = f"[{', '.join(str(x) for x in query_embedding)}]"
            sql = (
                "SELECT node_id, embedding FROM embeddings "
                f"ORDER BY embedding <-> {vector_literal} LIMIT {k}"
            )
            rows = conn.execute(sql).fetchall()
            return [{"node_id": r[0], "embedding": r[1]} for r in rows]
        except Exception as e:
            log.error(f"Vector search failed: {e}")
            return []

    @staticmethod
    def get_graph() -> nx.DiGraph[Any]:
        if _delegate and _delegate is not StorageManager:
            return _delegate.get_graph()
        with _lock:
            if _graph is None:
                setup()
            assert _graph is not None
            return _graph

    @staticmethod
    def touch_node(node_id: str) -> None:
        """Update access time for a node in the LRU cache or delegate."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.touch_node(node_id)
        with _lock:
            if node_id in _lru:
                _lru[node_id] = time.time()
                _lru.move_to_end(node_id)

    @staticmethod
    def get_duckdb_conn() -> duckdb.DuckDBPyConnection:
        if _delegate and _delegate is not StorageManager:
            return _delegate.get_duckdb_conn()
        with _lock:
            if _db_conn is None:
                setup()
            assert _db_conn is not None
            return _db_conn

    @staticmethod
    def get_rdf_store() -> rdflib.Graph:
        if _delegate and _delegate is not StorageManager:
            return _delegate.get_rdf_store()
        with _lock:
            if _rdf_store is None:
                setup()
            assert _rdf_store is not None
            return _rdf_store

    @staticmethod
    def clear_all() -> None:
        if _delegate and _delegate is not StorageManager:
            return _delegate.clear_all()
        with _lock:
            if _graph is not None:
                _graph.clear()
            if _db_conn is not None:
                _db_conn.execute("DELETE FROM nodes")
                _db_conn.execute("DELETE FROM edges")
                _db_conn.execute("DELETE FROM embeddings")
            if _rdf_store is not None:
                _rdf_store.remove((None, None, None))
