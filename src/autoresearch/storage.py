"""
Hybrid DKG persistence: NetworkX, DuckDB, RDFLib.
"""
import os
from threading import Lock
from typing import Optional

import duckdb
import networkx as nx
import rdflib

# Global containers initialised in `setup`
_graph: Optional[nx.DiGraph] = None
_db_path: Optional[str] = None
_db_conn: Optional[duckdb.DuckDBPyConnection] = None
_rdf_store: Optional[rdflib.Graph] = None
_lock = Lock()


def setup(db_path: Optional[str] = None) -> None:
    """Initialise storage components if not already initialised."""
    global _graph, _db_path, _db_conn, _rdf_store
    with _lock:
        if _db_conn is not None:
            return

        _graph = nx.DiGraph()
        _db_path = db_path or os.getenv("DUCKDB_PATH", "kg.duckdb")
        _db_conn = duckdb.connect(_db_path)
        _rdf_store = rdflib.Graph()

        # Ensure required tables exist
        _db_conn.execute(
            "CREATE TABLE IF NOT EXISTS nodes(id VARCHAR, type VARCHAR, content VARCHAR, conf DOUBLE, ts TIMESTAMP)"
        )
        _db_conn.execute(
            "CREATE TABLE IF NOT EXISTS edges(src VARCHAR, dst VARCHAR, rel VARCHAR, w DOUBLE)"
        )
        _db_conn.execute(
            "CREATE TABLE IF NOT EXISTS embeddings(node_id VARCHAR, embedding DOUBLE[])"
        )


def teardown(remove_db: bool = False) -> None:
    """Close connections and optionally remove the DuckDB file."""
    global _graph, _db_path, _db_conn, _rdf_store
    with _lock:
        if _db_conn is not None:
            _db_conn.close()
        if remove_db and _db_path and os.path.exists(_db_path):
            os.remove(_db_path)
        _graph = None
        _db_conn = None
        _rdf_store = None

class StorageManager:
    @staticmethod
    def persist_claim(claim: dict):
        """Persist claim to NetworkX, DuckDB, and RDFLib."""
        with _lock:
            if _db_conn is None:
                setup()
            # NetworkX
            _graph.add_node(claim['id'], **claim.get('attributes', {}))
            for rel in claim.get('relations', []):
                _graph.add_edge(rel['src'], rel['dst'], **rel.get('attributes', {}))
            # DuckDB
            # insert node row
            _db_conn.execute(
                "INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                [
                    claim['id'],
                    claim.get('type', ''),
                    claim.get('content', ''),
                    claim.get('confidence', 0.0),
                ]
            )
            # insert edges
            for rel in claim.get('relations', []):
                _db_conn.execute(
                    "INSERT INTO edges VALUES (?, ?, ?, ?)",
                    [
                        rel['src'],
                        rel['dst'],
                        rel.get('rel', ''),
                        rel.get('weight', 1.0),
                    ]
                )
            # insert embedding
            embedding = claim.get('embedding')
            if embedding is not None:
                _db_conn.execute(
                    "INSERT INTO embeddings VALUES (?, ?)",
                    [claim['id'], embedding]
                )
            # RDFLib quad persistence
            subj = rdflib.URIRef(f"urn:claim:{claim['id']}")
            for k,v in claim.get('attributes', {}).items():
                pred = rdflib.URIRef(f"urn:prop:{k}")
                obj = rdflib.Literal(v)
                _rdf_store.add((subj, pred, obj))

    @staticmethod
    def get_graph():
        with _lock:
            if _graph is None:
                setup()
            return _graph

    @staticmethod
    def get_duckdb_conn():
        with _lock:
            if _db_conn is None:
                setup()
            return _db_conn

    @staticmethod
    def get_rdf_store():
        with _lock:
            if _rdf_store is None:
                setup()
            return _rdf_store

    @staticmethod
    def clear_all():
        with _lock:
            if _graph is not None:
                _graph.clear()
            if _db_conn is not None:
                _db_conn.execute("DELETE FROM nodes")
                _db_conn.execute("DELETE FROM edges")
                _db_conn.execute("DELETE FROM embeddings")
            if _rdf_store is not None:
                _rdf_store.remove((None, None, None))


# Initialise storage on module import using default path
setup()

