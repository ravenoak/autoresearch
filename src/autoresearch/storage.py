"""
Hybrid DKG persistence: NetworkX, DuckDB, RDFLib.
"""
import os
import networkx as nx
import duckdb
import rdflib
from threading import Lock

# Initialize persistent components
_graph = nx.DiGraph()
_db_path = os.getenv("DUCKDB_PATH", "kg.duckdb")
_db_conn = duckdb.connect(_db_path)
_rdf_store = rdflib.Graph()
_lock = Lock()

# Ensure required DuckDB tables exist
_db_conn.execute("CREATE TABLE IF NOT EXISTS nodes(id VARCHAR, type VARCHAR, content VARCHAR, conf DOUBLE, ts TIMESTAMP)")
_db_conn.execute("CREATE TABLE IF NOT EXISTS edges(src VARCHAR, dst VARCHAR, rel VARCHAR, w DOUBLE)")
_db_conn.execute("CREATE TABLE IF NOT EXISTS embeddings(node_id VARCHAR, embedding LIST<DOUBLE>)")

class StorageManager:
    @staticmethod
    def persist_claim(claim: dict):
        """Persist claim to NetworkX, DuckDB, and RDFLib."""
        with _lock:
            # NetworkX
            _graph.add_node(claim['id'], **claim.get('attributes', {}))
            for rel in claim.get('relations', []):
                _graph.add_edge(rel['src'], rel['dst'], **rel.get('attributes', {}))
            # DuckDB
            # insert node row
            _db_conn.execute(
                "INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                [claim['id'], claim.get('type',''), claim.get('content',''), claim.get('confidence',0.0)]
            )
            # insert edges
            for rel in claim.get('relations', []):
                _db_conn.execute(
                    "INSERT INTO edges VALUES (?, ?, ?, ?)",
                    [rel['src'], rel['dst'], rel.get('rel',''), rel.get('weight',1.0)]
                )
            # insert embedding
            embedding = claim.get('embedding')
            if embedding:
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
        return _graph

    @staticmethod
    def get_duckdb_conn():
        return _db_conn

    @staticmethod
    def get_rdf_store():
        return _rdf_store

    @staticmethod
    def clear_all():
        with _lock:
            _graph.clear()
            _db_conn.execute("DELETE FROM nodes")
            _db_conn.execute("DELETE FROM edges")
            _db_conn.execute("DELETE FROM embeddings")
            _rdf_store.remove((None, None, None))

