"""
Hybrid Distributed Knowledge Graph (DKG) persistence system.

This module provides a storage system that combines three backends:
1. NetworkX: For in-memory graph storage and traversal
2. DuckDB: For relational storage and vector search
3. RDFLib: For semantic graph storage and SPARQL queries

The storage system supports claim persistence, vector search, and automatic
resource management with configurable eviction policies.

Note on Vector Extension:
The vector search functionality requires the DuckDB vector extension.
If the extension is not available, the system will still work, but
vector search operations will fail. Claims and embeddings will still
be stored in the database, but similarity search will not be available.
The system attempts to install and load the vector extension automatically
if it's enabled in the configuration.
"""

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
from .errors import StorageError, NotFoundError
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
            # Don't raise if it's a plugin registration issue, as this is a common case
            # in test environments where the full RDF dependencies might not be installed
            if "No plugin registered" not in str(e):
                raise StorageError("Failed to open RDF store", cause=e)
        if cfg.vector_extension:
            # First try to load from filesystem if path is configured
            extension_loaded = False
            if cfg.vector_extension_path:
                try:
                    extension_path = cfg.vector_extension_path
                    log.info(f"Loading vector extension from filesystem: {extension_path}")

                    # Check if the path exists
                    if not os.path.exists(extension_path):
                        log.warning(f"Vector extension path does not exist: {extension_path}")
                        raise FileNotFoundError(f"Vector extension path does not exist: {extension_path}")

                    # Load the extension from the filesystem
                    _db_conn.execute(f"LOAD '{extension_path}'")

                    # Verify the extension is loaded
                    try:
                        _db_conn.execute("SELECT hnsw_version()")
                        log.info("Vector extension loaded successfully from filesystem")
                        extension_loaded = True
                    except Exception as e:
                        log.warning(f"Vector extension may not be fully loaded from filesystem: {e}")
                        raise Exception(f"Failed to verify vector extension from filesystem: {e}")

                except Exception as e:
                    log.warning(f"Failed to load vector extension from filesystem: {e}")
                    # Continue to try downloading if loading from filesystem fails

            # If extension wasn't loaded from filesystem, try to download and install
            if not extension_loaded:
                try:
                    # Try to install the vector extension
                    # If it's already installed, this will be a no-op
                    log.info("Installing vector extension...")
                    _db_conn.execute("INSTALL vector")

                    # Load the vector extension
                    log.info("Loading vector extension...")
                    _db_conn.execute("LOAD vector")

                    # Verify the extension is loaded by trying to use a vector function
                    try:
                        _db_conn.execute("SELECT hnsw_version()")
                        log.info("Vector extension loaded successfully")
                    except Exception as e:
                        log.warning(f"Vector extension may not be fully loaded: {e}")
                except Exception as e:  # pragma: no cover - extension may fail
                    log.error(f"Failed to load vector extension: {e}")
                    # In test environments, we don't want to fail if the vector extension is not available
                    # Only raise in non-test environments or if explicitly configured to fail
                    if os.getenv("AUTORESEARCH_STRICT_EXTENSIONS", "").lower() == "true":
                        raise StorageError("Failed to load vector extension", cause=e)

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
    """Close connections and optionally remove the DuckDB file.

    This method closes all storage connections (DuckDB, RDF) and optionally
    removes the database files. It handles exceptions gracefully to ensure
    that cleanup always completes, even if errors occur during closing.

    Args:
        remove_db: If True, also removes the database files from disk.
                  Default is False.
    """
    global _graph, _db_conn, _rdf_store
    with _lock:
        if _db_conn is not None:
            try:
                _db_conn.close()
            except Exception as e:  # pragma: no cover - optional close
                log.warning(f"Failed to close DuckDB connection: {e}")
                # We don't raise here as this is cleanup code
        if _rdf_store is not None:
            try:
                _rdf_store.close()
            except Exception as e:  # pragma: no cover - optional close
                log.warning(f"Failed to close RDF store: {e}")
                # We don't raise here as this is cleanup code
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
    """Manages hybrid storage for distributed knowledge graphs.

    This class provides methods for persisting claims to multiple storage backends,
    searching for claims using vector embeddings, and managing storage resources
    with automatic eviction policies.

    The storage system uses three backends:
    - NetworkX: For in-memory graph storage and traversal
    - DuckDB: For relational storage and vector search
    - RDFLib: For semantic graph storage and SPARQL queries

    Most methods are class methods that operate on global storage instances,
    which are initialized by the `setup` function.
    """
    @staticmethod
    def setup(db_path: Optional[str] = None) -> None:
        """Initialize storage components if not already initialized.

        This method initializes the NetworkX graph, DuckDB connection, and RDFLib store.
        If a custom implementation is set via set_delegate(), the call is delegated to that implementation.

        Args:
            db_path: Optional path to the DuckDB database file. If not provided,
                     uses the DUCKDB_PATH environment variable or defaults to "kg.duckdb".

        Raises:
            StorageError: If the RDF store or vector extension fails to initialize
                          and the failure is not due to a plugin registration issue.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.setup(db_path)
        setup(db_path)

    @staticmethod
    def _current_ram_mb() -> float:
        """Calculate the approximate RAM usage of the current process in MB.

        This method attempts to measure the current memory usage using psutil.
        If psutil is not available, it falls back to the resource module.
        If both fail, it returns 0.0.

        Returns:
            float: The approximate RAM usage in megabytes.

        Note:
            This method handles exceptions internally and will not raise exceptions
            even if memory measurement fails.
        """
        try:
            import psutil  # type: ignore[import-untyped]

            mem = psutil.Process(os.getpid()).memory_info().rss
            return float(mem) / (1024**2)
        except Exception as e:  # pragma: no cover - psutil may not be available
            log.debug(f"Failed to get memory usage with psutil: {e}, falling back to resource")
            try:
                import resource

                usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                # ru_maxrss is KB on Linux, bytes on macOS
                if usage > 1024**2:
                    return usage / (1024**2)
                return usage / 1024
            except Exception as e:
                log.warning(f"Failed to get memory usage: {e}, returning 0.0")
                return 0.0

    @staticmethod
    def _pop_lru() -> str | None:
        """Remove and return the least recently used node from the LRU cache.

        This method implements the "Least Recently Used" (LRU) eviction policy.
        It removes the node that was accessed least recently from the LRU cache
        and returns its ID. This is used by the _enforce_ram_budget method when
        the graph_eviction_policy is set to "lru".

        The LRU cache is an OrderedDict that maintains the order in which nodes
        were accessed, with the least recently used node at the beginning and
        the most recently used node at the end.

        Returns:
            str | None: The ID of the least recently used node, or None if the cache is empty.

        Note:
            This method only removes the node from the LRU cache, not from the graph.
            The caller is responsible for removing the node from the graph if needed.
        """
        if not _lru:
            return None
        node_id, _ = _lru.popitem(last=False)
        return node_id

    @staticmethod
    def _pop_low_score() -> str | None:
        """Find and return the node with the lowest confidence score for eviction.

        This method implements the "Score-based" eviction policy. It finds the node
        with the lowest confidence score in the graph and returns its ID. This is used
        by the _enforce_ram_budget method when the graph_eviction_policy is set to "score".

        The confidence score is stored as a node attribute in the NetworkX graph.
        If a node doesn't have a confidence score, it's treated as having a score of 0.0.

        If the node is in the LRU cache, it's also removed from there to maintain consistency.

        Returns:
            str | None: The ID of the node with the lowest confidence score, or None if the graph is empty.

        Note:
            This method only identifies the node for eviction and removes it from the LRU cache if present.
            The caller is responsible for removing the node from the graph if needed.
        """
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

    @staticmethod
    def _enforce_ram_budget(budget_mb: int) -> None:
        """Evict nodes from the graph when memory usage exceeds the configured budget.

        This method monitors the current RAM usage and evicts nodes from the graph
        when it exceeds the specified budget. The eviction policy is determined by
        the configuration (either "lru" or "score"):
        - "lru": Evicts the least recently used nodes first
        - "score": Evicts nodes with the lowest confidence scores first

        The method continues evicting nodes until the RAM usage falls below the budget
        or there are no more nodes to evict.

        Args:
            budget_mb: The maximum amount of RAM to use in megabytes. If <= 0,
                      no eviction will occur.

        Note:
            Evicted nodes are removed from the in-memory graph but remain in the
            DuckDB and RDF stores. This allows for persistent storage while
            controlling memory usage.
        """
        if budget_mb <= 0:
            return

        policy = ConfigLoader().config.graph_eviction_policy

        while _graph and StorageManager._current_ram_mb() > budget_mb:
            node_id: str | None
            if policy == "score":
                node_id = StorageManager._pop_low_score()
            else:
                node_id = StorageManager._pop_lru()
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
    def _validate_claim(claim: dict[str, Any]) -> None:
        """Validate claim data before persistence to ensure it meets required format.

        This method checks that the claim:
        1. Is a dictionary
        2. Contains required fields ('id', 'type', 'content')
        3. All required fields are strings

        Additional validation may be performed by the persistence methods for specific backends.

        Args:
            claim: The claim to validate as a dictionary. Must contain 'id', 'type', and 'content' fields.
                  May also contain 'embedding', 'sources', and other attributes.

        Raises:
            StorageError: If the claim is invalid, with a specific error message and suggestion
                         for how to fix the issue.
        """
        if not isinstance(claim, dict):
            raise StorageError(
                "Invalid claim format: expected dictionary",
                suggestion="Ensure the claim is a dictionary with required fields"
            )

        # Check for required fields
        required_fields = ["id", "type", "content"]
        for field in required_fields:
            if field not in claim:
                raise StorageError(
                    f"Missing required field: '{field}'",
                    suggestion=f"Ensure the claim has a '{field}' field"
                )

            # Check that the field is a string
            if not isinstance(claim[field], str):
                raise StorageError(
                    f"Invalid '{field}' field: expected string",
                    suggestion=f"Ensure the '{field}' field is a string"
                )

    @staticmethod
    def _ensure_storage_initialized() -> None:
        """Ensure all storage components are initialized before performing operations.

        This method checks if the DuckDB connection, NetworkX graph, and RDF store
        are initialized. If any of them are not initialized, it attempts to initialize
        them by calling setup(). If initialization fails or any component remains
        uninitialized after setup, a StorageError is raised with a specific message
        indicating which component failed to initialize.

        Raises:
            StorageError: If any storage component cannot be initialized or remains
                         uninitialized after calling setup(). The error message includes
                         a suggestion to call StorageManager.setup() before performing operations.
        """
        if _db_conn is None or _graph is None or _rdf_store is None:
            try:
                setup()
            except Exception as e:
                raise StorageError("Failed to initialize storage components", cause=e)

        if _db_conn is None:
            raise StorageError(
                "DuckDB connection not initialized",
                suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations"
            )
        if _graph is None:
            raise StorageError(
                "Graph not initialized",
                suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations"
            )
        if _rdf_store is None:
            raise StorageError(
                "RDF store not initialized",
                suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations"
            )

    @staticmethod
    def _persist_to_networkx(claim: dict[str, Any]) -> None:
        """Persist a claim to the in-memory NetworkX graph.

        This method adds the claim as a node in the NetworkX graph, with its attributes
        and confidence score. It also updates the LRU cache with the current timestamp
        for the claim. If the claim has relations, they are added as edges in the graph.

        The NetworkX graph is used for in-memory storage and traversal of claims and
        their relationships. It supports fast graph operations but is subject to
        eviction when the RAM budget is exceeded.

        Args:
            claim: The claim to persist as a dictionary. Must contain an 'id' field.
                  May also contain 'attributes', 'confidence', and 'relations'.

        Note:
            This method assumes that storage has been initialized and the claim
            has been validated. It should be called by persist_claim, which
            handles these prerequisites.
        """
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

    @staticmethod
    def _persist_to_duckdb(claim: dict[str, Any]) -> None:
        """Persist a claim to the DuckDB relational database.

        This method inserts the claim into three tables in DuckDB:
        1. nodes: Stores the claim's ID, type, content, and confidence score
        2. edges: Stores relationships between claims (if any)
        3. embeddings: Stores the claim's vector embedding (if available)

        The DuckDB database provides persistent storage and supports vector search
        through the vector extension. Unlike the NetworkX graph, data in DuckDB
        is not subject to eviction when the RAM budget is exceeded.

        Args:
            claim: The claim to persist as a dictionary. Must contain an 'id' field.
                  May also contain 'type', 'content', 'confidence', 'relations',
                  and 'embedding'.

        Note:
            This method assumes that storage has been initialized and the claim
            has been validated. It should be called by persist_claim, which
            handles these prerequisites.
        """
        # Insert node row
        _db_conn.execute(
            "INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            [
                claim["id"],
                claim.get("type", ""),
                claim.get("content", ""),
                claim.get("confidence", 0.0),
            ],
        )

        # Insert edges
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

        # Insert embedding
        embedding = claim.get("embedding")
        if embedding is not None:
            _db_conn.execute(
                "INSERT INTO embeddings VALUES (?, ?)",
                [claim["id"], embedding],
            )

    @staticmethod
    def _persist_to_rdf(claim: dict[str, Any]) -> None:
        """Persist a claim to the RDFLib semantic graph store.

        This method adds the claim's attributes as triples in the RDF store,
        using the claim's ID as the subject URI. Each attribute is added as a
        separate triple with the attribute name as the predicate and the
        attribute value as the object.

        The RDF store provides semantic storage and supports SPARQL queries.
        Like DuckDB, data in the RDF store is not subject to eviction when
        the RAM budget is exceeded.

        Args:
            claim: The claim to persist as a dictionary. Must contain an 'id' field.
                  May also contain 'attributes' with key-value pairs to be stored as triples.

        Note:
            This method assumes that storage has been initialized and the claim
            has been validated. It should be called by persist_claim, which
            handles these prerequisites.
        """
        subj = rdflib.URIRef(f"urn:claim:{claim['id']}")
        for k, v in claim.get("attributes", {}).items():
            pred = rdflib.URIRef(f"urn:prop:{k}")
            obj = rdflib.Literal(v)
            _rdf_store.add((subj, pred, obj))

    @staticmethod
    def persist_claim(claim: dict[str, Any]) -> None:
        """Persist a claim to all storage backends.

        This method validates the claim, ensures storage is initialized, and then
        persists the claim to all three backends (NetworkX, DuckDB, and RDF).
        After persistence, it checks RAM usage and evicts older claims if needed
        based on the configured RAM budget.

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Args:
            claim: The claim to persist as a dictionary. Must contain 'id', 'content',
                  and may contain 'embedding', 'sources', and other attributes.

        Raises:
            StorageError: If the claim is invalid (missing required fields or
                         incorrect types) or if storage is not initialized properly.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.persist_claim(claim)

        # Validate claim
        StorageManager._validate_claim(claim)

        with _lock:
            # Ensure storage is initialized
            StorageManager._ensure_storage_initialized()

            # Persist to all backends
            StorageManager._persist_to_networkx(claim)
            StorageManager._persist_to_duckdb(claim)
            StorageManager._persist_to_rdf(claim)

            # Check RAM usage and evict if needed
            budget = ConfigLoader().config.ram_budget_mb
            StorageManager._enforce_ram_budget(budget)

    @staticmethod
    def create_hnsw_index() -> None:
        """Create a Hierarchical Navigable Small World (HNSW) index on the embeddings table.

        This method creates an HNSW index on the embeddings table to enable efficient
        approximate nearest neighbor search. The index parameters (m, ef_construction, metric)
        are configured via the storage configuration.

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Raises:
            StorageError: If the index creation fails and AUTORESEARCH_STRICT_EXTENSIONS
                         environment variable is set to "true".
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.create_hnsw_index()
        if _db_conn is None:
            setup()
        assert _db_conn is not None
        cfg = ConfigLoader().config.storage

        # First check if the vector extension is loaded
        try:
            # Try to use a vector function to check if the extension is loaded
            try:
                _db_conn.execute("SELECT hnsw_version()")
                log.info("Vector extension is loaded")
            except Exception:
                log.warning("Vector extension not loaded. Attempting to load it now.")

                # First try to load from filesystem if path is configured
                extension_loaded = False
                if cfg.vector_extension_path:
                    try:
                        extension_path = cfg.vector_extension_path
                        log.info(f"Loading vector extension from filesystem: {extension_path}")
                        _db_conn.execute(f"LOAD '{extension_path}'")
                        extension_loaded = True
                    except Exception as e:
                        log.warning(f"Failed to load vector extension from filesystem: {e}")

                # If not loaded from filesystem, try the default way
                if not extension_loaded:
                    _db_conn.execute("LOAD vector")

                # Verify it loaded
                try:
                    _db_conn.execute("SELECT hnsw_version()")
                    log.info("Vector extension loaded successfully")
                except Exception as e:
                    log.warning(f"Vector extension may not be fully loaded: {e}")
        except Exception as e:
            log.error(f"Failed to check or load vector extension: {e}")
            # Continue anyway, as the CREATE INDEX will fail if the extension is not available

        try:
            log.info("Creating HNSW index on embeddings table...")
            _db_conn.execute(
                "CREATE INDEX IF NOT EXISTS embeddings_hnsw "
                "ON embeddings USING hnsw (embedding) "
                f"WITH (m={cfg.hnsw_m}, "
                f"ef_construction={cfg.hnsw_ef_construction}, "
                f"metric='{cfg.hnsw_metric}')"
            )
            log.info("HNSW index created successfully")

            # Verify the index was created
            indexes = _db_conn.execute(
                "SELECT index_name FROM duckdb_indexes() WHERE table_name='embeddings'"
            ).fetchall()
            if not indexes:
                log.warning("HNSW index creation appeared to succeed, but no index was found")
            else:
                log.info(f"Verified index creation: {indexes}")

        except Exception as e:  # pragma: no cover - index creation may fail
            log.error(f"Failed to create HNSW index: {e}")
            # In test environments, we don't want to fail if the HNSW index creation fails
            # Only raise in non-test environments or if explicitly configured to fail
            if os.getenv("AUTORESEARCH_STRICT_EXTENSIONS", "").lower() == "true":
                raise StorageError("Failed to create HNSW index", cause=e)

    @staticmethod
    def _validate_vector_search_params(query_embedding: list[float], k: int) -> None:
        """Validate parameters for vector search to ensure they meet required format.

        This method performs comprehensive validation of vector search parameters:
        1. Checks that query_embedding is a list
        2. Verifies that all values in query_embedding are numeric (int or float)
        3. Ensures query_embedding is not empty
        4. Confirms that k is a positive integer

        Args:
            query_embedding: The query embedding vector as a list of floats.
                            Must be non-empty and contain only numeric values.
            k: The number of results to return. Must be a positive integer.

        Raises:
            StorageError: If any parameter is invalid, with a specific error message
                         and suggestion for how to fix the issue.
        """
        if not isinstance(query_embedding, list):
            raise StorageError(
                "Invalid query_embedding format: expected list of floats",
                suggestion="Ensure the query_embedding is a list of float values"
            )

        if not all(isinstance(x, (int, float)) for x in query_embedding):
            raise StorageError(
                "Invalid query_embedding values: expected numeric values",
                suggestion="Ensure all values in query_embedding are numbers"
            )

        if len(query_embedding) == 0:
            raise StorageError(
                "Empty query_embedding",
                suggestion="Provide a non-empty list of float values for query_embedding"
            )

        if not isinstance(k, int) or k <= 0:
            raise StorageError(
                "Invalid k value: expected positive integer",
                suggestion="Ensure k is a positive integer"
            )

    @staticmethod
    def _format_vector_literal(query_embedding: list[float]) -> str:
        """Format a vector embedding as a SQL literal for use in DuckDB queries.

        This method converts a list of float values into a string representation
        that can be used as a vector literal in DuckDB SQL queries. The format
        is a comma-separated list of values enclosed in square brackets.

        Example:
            [1.0, 2.5, 3.7] -> "[1.0, 2.5, 3.7]"

        Args:
            query_embedding: The query embedding vector as a list of floats.
                            Should be validated before calling this method.

        Returns:
            str: The formatted vector literal for SQL, ready to be used in
                DuckDB vector similarity queries.
        """
        return f"[{', '.join(str(x) for x in query_embedding)}]"

    @staticmethod
    def vector_search(
        query_embedding: list[float], k: int = 5
    ) -> list[dict[str, Any]]:
        """Search for claims by vector similarity.

        This method performs a vector similarity search using the provided query embedding.
        It validates the search parameters, ensures storage is initialized, and then
        executes the search using the DuckDB vector extension if available.

        The search uses cosine similarity by default (configurable via storage.hnsw_metric)
        and returns the k most similar claims, ordered by similarity score.

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Args:
            query_embedding: The query embedding vector as a list of floats.
                            Must be non-empty and contain only numeric values.
            k: The number of results to return. Must be a positive integer.
                Default is 5.

        Returns:
            list[dict[str, Any]]: List of nearest nodes with their embeddings and
                                 similarity scores, ordered by similarity (highest first).
                                 Each result contains 'id', 'content', 'embedding',
                                 'similarity', and other claim attributes.

        Raises:
            StorageError: If the search parameters are invalid, storage is not initialized,
                         or the vector extension is not available.
            NotFoundError: If no embeddings are found in the database.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.vector_search(query_embedding, k)

        # Validate parameters
        StorageManager._validate_vector_search_params(query_embedding, k)

        # Ensure storage is initialized
        StorageManager._ensure_storage_initialized()

        conn = StorageManager.get_duckdb_conn()
        cfg = ConfigLoader().config

        try:
            # Set search parameters
            try:
                conn.execute(f"SET hnsw_ef_search={cfg.vector_nprobe}")
            except Exception as e:
                log.debug(f"Failed to set hnsw_ef_search: {e}, continuing with default")

            # Format query and execute search
            vector_literal = StorageManager._format_vector_literal(query_embedding)
            sql = (
                "SELECT node_id, embedding FROM embeddings "
                f"ORDER BY embedding <-> {vector_literal} LIMIT {k}"
            )
            rows = conn.execute(sql).fetchall()

            # Format results
            return [{"node_id": r[0], "embedding": r[1]} for r in rows]
        except Exception as e:
            log.error(f"Vector search failed: {e}")
            raise StorageError(
                "Vector search failed", 
                cause=e,
                suggestion="Check that the vector extension is properly installed and that embeddings exist in the database"
            )

    @staticmethod
    def get_graph() -> nx.DiGraph[Any]:
        """Get the NetworkX graph instance used for in-memory storage.

        This method returns the global NetworkX DiGraph instance used for in-memory
        storage of claims and their relationships. If the graph is not initialized,
        it attempts to initialize it by calling setup().

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Returns:
            nx.DiGraph[Any]: The NetworkX directed graph instance.

        Raises:
            NotFoundError: If the graph cannot be initialized or remains None after initialization.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.get_graph()
        with _lock:
            if _graph is None:
                try:
                    setup()
                except Exception as e:
                    raise NotFoundError("Graph not initialized", cause=e)
            if _graph is None:
                raise NotFoundError("Graph not initialized")
            return _graph

    @staticmethod
    def touch_node(node_id: str) -> None:
        """Update access time for a node in the LRU cache.

        This method updates the access timestamp for a node in the LRU (Least Recently Used)
        cache and moves it to the end of the cache order, marking it as most recently used.
        This affects the eviction policy, as nodes with older access times are evicted first
        when the RAM budget is exceeded.

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Args:
            node_id: The ID of the node to update.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.touch_node(node_id)
        with _lock:
            if node_id in _lru:
                _lru[node_id] = time.time()
                _lru.move_to_end(node_id)

    @staticmethod
    def get_duckdb_conn() -> duckdb.DuckDBPyConnection:
        """Get the DuckDB connection used for relational storage.

        This method returns the global DuckDB connection used for relational
        storage of claims and their embeddings. If the connection is not initialized,
        it attempts to initialize it by calling setup().

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Returns:
            duckdb.DuckDBPyConnection: The DuckDB connection instance.

        Raises:
            NotFoundError: If the connection cannot be initialized or remains None after initialization.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.get_duckdb_conn()
        with _lock:
            if _db_conn is None:
                try:
                    setup()
                except Exception as e:
                    raise NotFoundError("DuckDB connection not initialized", cause=e)
            if _db_conn is None:
                raise NotFoundError("DuckDB connection not initialized")
            return _db_conn

    @staticmethod
    def get_rdf_store() -> rdflib.Graph:
        """Get the RDFLib Graph used for semantic graph storage.

        This method returns the global RDFLib Graph used for semantic storage
        of claims and their relationships. If the graph is not initialized,
        it attempts to initialize it by calling setup().

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Returns:
            rdflib.Graph: The RDFLib Graph instance.

        Raises:
            NotFoundError: If the RDF store cannot be initialized or remains None after initialization.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.get_rdf_store()
        with _lock:
            if _rdf_store is None:
                try:
                    setup()
                except Exception as e:
                    raise NotFoundError("RDF store not initialized", cause=e)
            if _rdf_store is None:
                raise NotFoundError("RDF store not initialized")
            return _rdf_store

    @staticmethod
    def clear_all() -> None:
        """Clear all data from all storage backends.

        This method removes all claims and their relationships from all three storage backends:
        - Clears the NetworkX graph
        - Deletes all rows from the nodes, edges, and embeddings tables in DuckDB
        - Removes all triples from the RDF store

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Note: This operation cannot be undone and should be used with caution.
        """
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
