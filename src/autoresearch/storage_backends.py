"""
Storage backend implementations for the autoresearch project.

This module provides storage backend classes that encapsulate the details
of interacting with different storage systems. The current implementation
focuses on DuckDB as the primary backend for relational storage and vector search.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional

from dotenv import dotenv_values

import duckdb

from .config import ConfigLoader
from .errors import NotFoundError, StorageError
from .extensions import VSSExtensionLoader
from .logging_utils import get_logger
from .orchestration.metrics import KUZU_QUERY_COUNTER, KUZU_QUERY_TIME
from .storage_utils import initialize_schema_version

# Use "Any" for DuckDB connection due to incomplete type hints in duckdb.
DuckDBConnection = Any

if TYPE_CHECKING:  # pragma: no cover - type hints only
    import kuzu

log = get_logger(__name__)


class DuckDBStorageBackend:
    """
    Encapsulates DuckDB connection and schema logic.

    This class manages the DuckDB connection, schema creation, and query execution.
    It provides methods for persisting claims, searching by vector similarity,
    and managing the database schema.

    The class is designed to be used by the StorageManager, which coordinates
    between multiple storage backends (DuckDB, NetworkX, RDFLib).
    """

    def __init__(self):
        """Initialize the DuckDB storage backend."""
        self._conn: Optional[DuckDBConnection] = None
        self._path: Optional[str] = None
        self._lock = Lock()
        self._has_vss: bool = False
        self._pool: Optional[Queue[DuckDBConnection]] = None
        self._max_connections: int = 1

    def setup(self, db_path: Optional[str] = None, skip_migrations: bool = False) -> None:
        """
        Initialize the DuckDB connection and create required tables.

        Args:
            db_path: Optional path to the DuckDB database file. If not provided,
                    the path is determined with the following precedence:
                    1. config.storage.duckdb.path
                    2. DUCKDB_PATH environment variable
                    3. Default to "kg.duckdb".
            skip_migrations: If True, skip running migrations after creating tables.
                            This is useful for testing.

        Raises:
            StorageError: If the connection cannot be established or tables cannot be created.
        """
        with self._lock:
            if self._conn is not None:
                return

            cfg = ConfigLoader().config.storage

            # Determine the database path with the following precedence:
            # 1. db_path parameter (for backward compatibility)
            # 2. config.storage.duckdb.path
            # 3. DUCKDB_PATH environment variable
            # 4. Default to "kg.duckdb"
            path: str = (
                db_path
                if db_path is not None
                else (
                    cfg.duckdb.path
                    if hasattr(cfg, "duckdb") and hasattr(cfg.duckdb, "path")
                    else os.getenv("DUCKDB_PATH", "kg.duckdb")
                )
            )
            memory_mode = path == ":memory:"
            # Preserve the provided path even for in-memory databases so tests
            # can assert on deterministic setup behaviour.
            self._path = path

            try:
                self._conn = duckdb.connect(path)
            except Exception as e:
                log.error(f"Failed to connect to DuckDB database: {e}")
                self._conn = None
                raise StorageError("Failed to connect to DuckDB database", cause=e)

            # Create connection pool unless using an in-memory database
            if memory_mode:
                self._max_connections = 1
                self._pool = None
            else:
                max_conn = getattr(cfg, "max_connections", 1)
                try:
                    self._max_connections = int(max_conn)
                except Exception:
                    self._max_connections = 1
                self._pool = Queue(maxsize=self._max_connections)
                self._pool.put(self._conn)
                for _ in range(self._max_connections - 1):
                    self._pool.put(duckdb.connect(path))

            # Load VSS extension if enabled
            if cfg.vector_extension:
                last_exc: Exception | None = None
                try:
                    self._has_vss = VSSExtensionLoader.load_extension(self._conn)
                    if self._has_vss:
                        log.info("VSS extension loaded successfully")
                    else:
                        log.warning("VSS extension not available")
                except (duckdb.Error, StorageError) as e:  # type: ignore[attr-defined]
                    log.error(f"Failed to load VSS extension: {e}")
                    self._has_vss = False
                    last_exc = e

                if not self._has_vss:
                    env_offline = Path(".env.offline")
                    if env_offline.exists():
                        offline_vars = dotenv_values(env_offline)
                        ext_path = offline_vars.get("VECTOR_EXTENSION_PATH")
                        if ext_path and "VECTOR_EXTENSION_PATH" not in os.environ:
                            os.environ["VECTOR_EXTENSION_PATH"] = ext_path
                            try:
                                self._has_vss = VSSExtensionLoader.load_extension(self._conn)
                                if self._has_vss:
                                    log.info("VSS extension loaded from offline cache")
                                else:
                                    log.warning("VSS extension offline fallback unavailable")
                            except (duckdb.Error, StorageError) as e:  # type: ignore[attr-defined]
                                log.error(f"Offline VSS load failed: {e}")
                                self._has_vss = False
                                last_exc = e

                if (
                    not self._has_vss
                    and os.getenv("AUTORESEARCH_STRICT_EXTENSIONS", "").lower() == "true"
                    and os.getenv("PYTEST_CURRENT_TEST") is None
                ):
                    raise StorageError("Failed to load VSS extension", cause=last_exc)

            # Ensure required tables exist
            self._create_tables(skip_migrations)

            # Create HNSW index if vector extension is enabled and available
            if cfg.vector_extension and self._has_vss:
                self.create_hnsw_index()

    def _create_tables(self, skip_migrations: bool = False) -> None:
        """
        Create the required tables in the DuckDB database.

        This method creates the following tables if they don't exist:
        - nodes: Stores claim nodes with ID, type, content, confidence, and timestamp
        - edges: Stores relationships between nodes
        - embeddings: Stores vector embeddings for nodes
        - metadata: Stores database metadata including schema_version

        Args:
            skip_migrations: If True, skip running migrations after creating tables.
                            This is useful for testing.

        Raises:
            StorageError: If the tables cannot be created.
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            # Create core tables
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS nodes("
                "id VARCHAR, type VARCHAR, content VARCHAR, "
                "conf DOUBLE, ts TIMESTAMP)"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS edges("
                "src VARCHAR, dst VARCHAR, rel VARCHAR, "
                "w DOUBLE)"
            )
            # Create embeddings table with a fixed dimension for the embedding column
            # Using FLOAT[384] instead of DOUBLE[] to ensure compatibility with HNSW index
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS embeddings(" "node_id VARCHAR, embedding FLOAT[384])"
            )

            # Create metadata table for schema versioning
            self._conn.execute("CREATE TABLE IF NOT EXISTS metadata(key VARCHAR, value VARCHAR)")

            # Initialize schema version if it doesn't exist
            self._initialize_schema_version()

            # Run migrations if needed and not skipped
            if not skip_migrations:
                self._run_migrations()

        except duckdb.Error as e:  # type: ignore[attr-defined]
            raise StorageError(f"DuckDB error while creating tables: {e}") from e
        except StorageError:
            raise
        except Exception as e:  # pragma: no cover - unexpected error path
            raise StorageError("Failed to create tables", cause=e)

    def _initialize_schema_version(self) -> None:
        """Delegate schema version initialization to a utility helper."""
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        initialize_schema_version(self._conn)

    def get_schema_version(self, initialize_if_missing: bool = True) -> Optional[int]:
        """
        Get the current schema version from the metadata table.

        Args:
            initialize_if_missing: If True, initialize the schema version to 1 if it doesn't exist.
                                  If False, return None if the schema version doesn't exist.

        Returns:
            The current schema version as an integer, or None if the schema version doesn't exist
            and initialize_if_missing is False.

        Raises:
            StorageError: If the schema version cannot be retrieved.
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            cursor = self._conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
            rows = cursor.fetchall()
            row = rows[0] if rows else None

            if row is None:
                if initialize_if_missing:
                    # This should not happen as _initialize_schema_version should have been called
                    log.warning("Schema version not found in metadata table, initializing to 1")
                    self._initialize_schema_version()
                    return 1
                else:
                    return None

            return int(row[0])
        except Exception as e:
            raise StorageError("Failed to get schema version", cause=e)

    def update_schema_version(self, version: int) -> None:
        """
        Update the schema version in the metadata table.

        Args:
            version: The new schema version to set.

        Raises:
            StorageError: If the schema version cannot be updated.
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            self._conn.execute(
                "UPDATE metadata SET value = ? WHERE key = 'schema_version'",
                [str(version)],
            )
            log.info(f"Updated schema version to {version}")
        except Exception as e:
            raise StorageError(f"Failed to update schema version to {version}", cause=e)

    def _run_migrations(self) -> None:
        """
        Run schema migrations based on the current schema version.

        This method checks the current schema version and runs any necessary
        migrations to bring the schema up to the latest version.

        Raises:
            StorageError: If migrations cannot be run.
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            current_version = self.get_schema_version()
            latest_version = 1  # Update this when adding new migrations

            log.info(f"Current schema version: {current_version}, latest version: {latest_version}")

            # Run migrations sequentially
            if current_version is None or current_version < latest_version:
                log.info(f"Running migrations from version {current_version} to {latest_version}")

                # Example migration pattern for future use:
                # if current_version < 2:
                #     self._migrate_to_v2()
                #     current_version = 2

                # Update schema version to latest
                self.update_schema_version(latest_version)

        except Exception as e:
            raise StorageError("Failed to run migrations", cause=e)

    def create_hnsw_index(self) -> None:
        """
        Create a Hierarchical Navigable Small World (HNSW) index on the embeddings table.

        This method creates an HNSW index on the embeddings table to enable efficient
        approximate nearest neighbor search. The index parameters (m, ef_construction, metric)
        are configured via the storage configuration.

        Raises:
            StorageError: If the index creation fails and AUTORESEARCH_STRICT_EXTENSIONS
                         environment variable is set to "true".
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        cfg = ConfigLoader().config.storage

        # Check if the VSS extension is loaded and load it if needed
        try:
            # Check if the VSS extension is loaded by querying duckdb_extensions()
            if not VSSExtensionLoader.verify_extension(self._conn, verbose=False):
                log.warning("VSS extension not loaded. Attempting to load it now.")
                VSSExtensionLoader.load_extension(self._conn)
            else:
                log.debug("VSS extension is already loaded")
        except Exception as e:
            log.error(f"Failed to check or load VSS extension: {e}")
            # Continue anyway, as the CREATE INDEX will fail if the extension is not available

        try:
            # Enable experimental persistence for HNSW indexes in persistent databases
            log.info("Enabling experimental persistence for HNSW indexes")
            self._conn.execute("SET hnsw_enable_experimental_persistence=true")

            log.info("Creating HNSW index on embeddings table...")
            # Ensure metric is one of the valid values: 'ip', 'cosine', 'l2sq'
            metric = cfg.hnsw_metric
            if metric not in ["ip", "cosine", "l2sq"]:
                log.warning(f"Invalid HNSW metric '{metric}', falling back to 'l2sq'")
                metric = "l2sq"

            # Check if the embeddings table is empty
            rows = self._conn.execute("SELECT COUNT(*) FROM embeddings").fetchall()
            count = rows[0][0] if rows else 0

            if count == 0:
                # If the table is empty, insert a dummy embedding to ensure the HNSW index can be created
                # Use a 384-dimensional vector (common for many embedding models)
                dummy_id = "__dummy_for_index__"
                dummy_embedding = [0.0] * 384
                try:
                    # Insert the dummy embedding
                    self._conn.execute(
                        "INSERT INTO embeddings VALUES (?, ?)",
                        [dummy_id, dummy_embedding],
                    )
                    log.debug("Inserted dummy embedding for HNSW index creation")
                except Exception as e:
                    log.warning(f"Failed to insert dummy embedding: {e}")

            try:
                # Create the HNSW index
                self._conn.execute(
                    "CREATE INDEX IF NOT EXISTS embeddings_hnsw "
                    "ON embeddings USING hnsw (embedding) "
                    f"WITH (m={cfg.hnsw_m}, "
                    f"ef_construction={cfg.hnsw_ef_construction}, "
                    f"metric='{metric}')"
                )

                # Set ef_search after index creation
                ef_search = getattr(cfg, "hnsw_ef_search", cfg.vector_nprobe)
                if getattr(cfg, "hnsw_auto_tune", False):
                    tuned = max(cfg.hnsw_m * 2, cfg.hnsw_ef_construction // 2)
                    if tuned > ef_search:
                        log.debug(f"Auto-tuned ef_search from {ef_search} to {tuned}")
                        ef_search = tuned
                try:
                    self._conn.execute(f"SET hnsw_ef_search={ef_search}")
                except Exception as e:
                    log.debug(f"Failed to set ef_search: {e}")

                # If we inserted a dummy embedding, remove it now
                if count == 0:
                    try:
                        self._conn.execute("DELETE FROM embeddings WHERE node_id = ?", [dummy_id])
                        log.debug("Removed dummy embedding after HNSW index creation")
                    except Exception as e:
                        log.warning(f"Failed to remove dummy embedding: {e}")
            except Exception as e:
                log.error(f"Failed to create HNSW index: {e}")
                raise
            log.info("HNSW index created successfully")

            # Verify the index was created
            indexes = self._conn.execute(
                "SELECT index_name FROM duckdb_indexes() WHERE table_name='embeddings'"
            ).fetchall()
            if not indexes:
                log.warning("HNSW index creation appeared to succeed, but no index was found")
            else:
                log.info(f"Verified index creation: {indexes}")

        except Exception as e:
            log.error(f"Failed to create HNSW index: {e}")
            # In test environments, we don't want to fail if the HNSW index creation fails
            # Only raise in non-test environments or if explicitly configured to fail
            if os.getenv("AUTORESEARCH_STRICT_EXTENSIONS", "").lower() == "true":
                raise StorageError("Failed to create HNSW index", cause=e)

    def refresh_hnsw_index(self) -> None:
        """Rebuild the HNSW index to include new embeddings."""
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        with self._lock:
            try:
                self._conn.execute("DROP INDEX IF EXISTS embeddings_hnsw")
                self.create_hnsw_index()
            except Exception as e:  # pragma: no cover - unexpected DB failure
                raise StorageError("Failed to refresh HNSW index", cause=e)

    def persist_claim(self, claim: Dict[str, Any]) -> None:
        """
        Persist a claim to the DuckDB database.

        This method inserts the claim into three tables in DuckDB:
        1. nodes: Stores the claim's ID, type, content, and confidence score
        2. edges: Stores relationships between claims (if any)
        3. embeddings: Stores the claim's vector embedding (if available)

        Args:
            claim: The claim to persist as a dictionary. Must contain an 'id' field.
                  May also contain 'type', 'content', 'confidence', 'relations',
                  and 'embedding'.

        Raises:
            StorageError: If the claim cannot be persisted.
        """
        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        with self.connection() as conn, self._lock:
            try:
                conn.execute(
                    "INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    [
                        claim["id"],
                        claim.get("type", ""),
                        claim.get("content", ""),
                        claim.get("confidence", 0.0),
                    ],
                )

                for rel in claim.get("relations", []):
                    conn.execute(
                        "INSERT INTO edges VALUES (?, ?, ?, ?)",
                        [
                            rel["src"],
                            rel["dst"],
                            rel.get("rel", ""),
                            rel.get("weight", 1.0),
                        ],
                    )

                embedding = claim.get("embedding")
                if embedding is not None:
                    conn.execute(
                        "INSERT INTO embeddings VALUES (?, ?)",
                        [claim["id"], embedding],
                    )
            except Exception as e:
                raise StorageError("Failed to persist claim to DuckDB", cause=e)

    def update_claim(self, claim: Dict[str, Any], partial_update: bool = False) -> None:
        """Update an existing claim in the DuckDB database.

        Parameters
        ----------
        claim:
            The claim data with at least an ``id`` field. Other fields are
            updated if provided.
        partial_update:
            If ``True`` only the supplied fields are updated, otherwise the
            existing rows are fully replaced.
        """
        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        with self.connection() as conn, self._lock:
            try:
                if not partial_update:
                    conn.execute(
                        "UPDATE nodes SET type=?, content=?, conf=?, ts=CURRENT_TIMESTAMP WHERE id=?",
                        [
                            claim.get("type", ""),
                            claim.get("content", ""),
                            claim.get("confidence", 0.0),
                            claim["id"],
                        ],
                    )
                else:
                    if "type" in claim:
                        conn.execute(
                            "UPDATE nodes SET type=? WHERE id=?",
                            [claim["type"], claim["id"]],
                        )
                    if "content" in claim:
                        conn.execute(
                            "UPDATE nodes SET content=? WHERE id=?",
                            [claim["content"], claim["id"]],
                        )
                    if "confidence" in claim:
                        conn.execute(
                            "UPDATE nodes SET conf=? WHERE id=?",
                            [claim["confidence"], claim["id"]],
                        )

                if "relations" in claim:
                    conn.execute(
                        "DELETE FROM edges WHERE src=? OR dst=?",
                        [claim["id"], claim["id"]],
                    )
                    for rel in claim.get("relations", []):
                        conn.execute(
                            "INSERT INTO edges VALUES (?, ?, ?, ?)",
                            [
                                rel["src"],
                                rel["dst"],
                                rel.get("rel", ""),
                                rel.get("weight", 1.0),
                            ],
                        )

                if "embedding" in claim:
                    conn.execute(
                        "DELETE FROM embeddings WHERE node_id=?",
                        [claim["id"]],
                    )
                    embedding = claim.get("embedding")
                    if embedding is not None:
                        conn.execute(
                            "INSERT INTO embeddings VALUES (?, ?)",
                            [claim["id"], embedding],
                        )
            except Exception as e:  # pragma: no cover - unexpected DB failure
                raise StorageError("Failed to update claim in DuckDB", cause=e)

    def vector_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        similarity_threshold: float = 0.0,
        include_metadata: bool = False,
        filter_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for claims by vector similarity with advanced options.

        This method performs an optimized vector similarity search using the provided query embedding.
        It uses the DuckDB VSS extension to find the k most similar claims, ordered by
        similarity score, with options for filtering and metadata inclusion.

        Args:
            query_embedding: The query embedding vector as a list of floats.
                           Must be non-empty and contain only numeric values.
            k: The number of results to return. Must be a positive integer.
               Default is 5.
            similarity_threshold: Minimum similarity score (0.0 to 1.0) for results.
                                 Default is 0.0 (no threshold).
            include_metadata: Whether to include node metadata in results.
                            Default is False.
            filter_types: Optional list of claim types to filter by.
                        Default is None (no filtering).

        Returns:
            List of nearest nodes with their embeddings and metadata, ordered by
            similarity (highest first). Each result contains 'node_id', 'embedding',
            'similarity', and optionally 'type', 'content', and 'confidence'.

        Raises:
            StorageError: If the search fails or the VSS extension is not available.
            NotFoundError: If no embeddings are found in the database.
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        # Check if VSS extension is available
        if not self._has_vss:
            raise StorageError(
                "Vector search not available: VSS extension not loaded",
                suggestion="Ensure the VSS extension is properly installed and enabled in the configuration",
            )

        cfg = ConfigLoader().config

        # Start timing for performance metrics
        import time

        start_time = time.time()

        try:
            # Set search parameters for better recall
            try:
                ef_search = getattr(cfg.storage, "hnsw_ef_search", cfg.storage.vector_nprobe)
                if getattr(cfg.storage, "hnsw_auto_tune", False):
                    tuned = max(cfg.storage.hnsw_m * 2, cfg.storage.hnsw_ef_construction // 2)
                    if tuned > ef_search:
                        log.debug(f"Auto-tuned ef_search from {ef_search} to {tuned}")
                        ef_search = tuned
                # Higher ef_search value improves recall at the cost of search speed
                self._conn.execute(f"SET hnsw_ef_search={ef_search}")

                # Set additional optimization parameters if available in config
                if hasattr(cfg, "vector_search_batch_size"):
                    self._conn.execute(f"SET vss_search_batch_size={cfg.vector_search_batch_size}")
            except Exception as e:
                log.debug(f"Failed to set search parameters: {e}, continuing with defaults")

            # Format query embedding as vector literal
            vector_literal = f"[{', '.join(str(x) for x in query_embedding)}]"

            # Build the SQL query with optimizations
            if include_metadata:
                # Join with nodes table to include metadata
                select_clause = """
                    e.node_id,
                    e.embedding,
                    n.type,
                    n.content,
                    n.confidence,
                    CASE
                        WHEN '{metric}' = 'cosine' THEN 1 - (e.embedding <-> {vector})
                        WHEN '{metric}' = 'ip' THEN 1 - (e.embedding <=> {vector})
                        ELSE 1 / (1 + (e.embedding <-> {vector}))
                    END AS similarity
                """.format(
                    vector=vector_literal,
                    metric=(
                        cfg.storage.hnsw_metric
                        if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric")
                        else "cosine"
                    ),
                )

                from_clause = "FROM embeddings e JOIN nodes n ON e.node_id = n.id"

                # Add type filtering if specified
                where_clause = ""
                if filter_types and len(filter_types) > 0:
                    type_list = ", ".join([f"'{t}'" for t in filter_types])
                    where_clause = f"WHERE n.type IN ({type_list})"

                # Add similarity threshold filtering
                if similarity_threshold > 0:
                    similarity_condition = f"""
                        CASE
                            WHEN '{cfg.storage.hnsw_metric if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric") else "cosine"}' = 'cosine' THEN 1 - (e.embedding <-> {vector_literal})
                            WHEN '{cfg.storage.hnsw_metric if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric") else "cosine"}' = 'ip' THEN 1 - (e.embedding <=> {vector_literal})
                            ELSE 1 / (1 + (e.embedding <-> {vector_literal}))
                        END >= {similarity_threshold}
                    """
                    where_clause = (
                        f"WHERE {similarity_condition}"
                        if not where_clause
                        else f"{where_clause} AND {similarity_condition}"
                    )

                # Order by similarity and limit results
                order_clause = f"ORDER BY e.embedding <-> {vector_literal} LIMIT {k}"

                # Combine all clauses
                sql = f"SELECT {select_clause} {from_clause} {where_clause} {order_clause}"
            else:
                # Simplified query without metadata
                select_clause = """
                    node_id,
                    embedding,
                    CASE
                        WHEN '{metric}' = 'cosine' THEN 1 - (embedding <-> {vector})
                        WHEN '{metric}' = 'ip' THEN 1 - (embedding <=> {vector})
                        ELSE 1 / (1 + (embedding <-> {vector}))
                    END AS similarity
                """.format(
                    vector=vector_literal,
                    metric=(
                        cfg.storage.hnsw_metric
                        if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric")
                        else "cosine"
                    ),
                )

                # Add similarity threshold filtering
                where_clause = ""
                if similarity_threshold > 0:
                    similarity_condition = f"""
                        CASE
                            WHEN '{cfg.storage.hnsw_metric if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric") else "cosine"}' = 'cosine' THEN 1 - (embedding <-> {vector_literal})
                            WHEN '{cfg.storage.hnsw_metric if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric") else "cosine"}' = 'ip' THEN 1 - (embedding <=> {vector_literal})
                            ELSE 1 / (1 + (embedding <-> {vector_literal}))
                        END >= {similarity_threshold}
                    """
                    where_clause = f"WHERE {similarity_condition}"

                # Order by similarity and limit results
                order_clause = f"ORDER BY embedding <-> {vector_literal} LIMIT {k}"

                # Combine all clauses
                sql = f"SELECT {select_clause} FROM embeddings {where_clause} {order_clause}"

            # Execute the query with a timeout
            try:
                # Set a query timeout if configured
                if hasattr(cfg, "vector_search_timeout_ms"):
                    self._conn.execute(f"SET query_timeout_ms={cfg.vector_search_timeout_ms}")

                # Execute the query
                rows = self._conn.execute(sql).fetchall()
            except Exception as e:
                log.warning(f"Vector search query failed, falling back to simpler query: {e}")
                # Fall back to a simpler query if the optimized one fails
                simple_sql = f"SELECT node_id, embedding FROM embeddings ORDER BY embedding <-> {vector_literal} LIMIT {k}"
                rows = self._conn.execute(simple_sql).fetchall()
                # Format results without metadata or similarity scores
                return [{"node_id": r[0], "embedding": r[1]} for r in rows]

            # Format results based on query type
            results = []
            if include_metadata:
                for r in rows:
                    result = {
                        "node_id": r[0],
                        "embedding": r[1],
                        "type": r[2],
                        "content": r[3],
                        "confidence": r[4],
                        "similarity": r[5],
                    }
                    results.append(result)
            else:
                for r in rows:
                    result = {"node_id": r[0], "embedding": r[1], "similarity": r[2]}
                    results.append(result)

            # Log performance metrics
            search_time = time.time() - start_time
            log.debug(f"Vector search completed in {search_time:.4f}s with {len(results)} results")

            return results
        except Exception as e:
            log.error(f"Vector search failed: {e}")
            raise StorageError(
                "Vector search failed",
                cause=e,
                suggestion="Check that the VSS extension is properly installed and that embeddings exist in the database",
            )

    def get_connection(self) -> DuckDBConnection:
        """
        Get the DuckDB connection.

        Returns:
            The DuckDB connection instance.

        Raises:
            NotFoundError: If the connection is not initialized.
        """
        if self._conn is None:
            raise NotFoundError("DuckDB connection not initialized")
        return self._conn

    @contextmanager
    def connection(self) -> Iterator[DuckDBConnection]:
        """Context manager that yields a connection from the pool."""
        if self._pool is None:
            if self._conn is None:
                raise NotFoundError("DuckDB connection not initialized")
            yield self._conn
            return
        conn = self._pool.get()
        try:
            yield conn
        finally:
            self._pool.put(conn)

    def has_vss(self) -> bool:
        """
        Check if the VSS extension is available.

        Returns:
            bool: True if the VSS extension is loaded and available, False otherwise.
        """
        return self._has_vss

    def close(self) -> None:
        """
        Close the DuckDB connection.

        This method closes the DuckDB connection and releases any resources.
        It handles exceptions gracefully to ensure that cleanup always completes,
        even if errors occur during closing.
        """
        with self._lock:
            if self._pool is not None:
                while not self._pool.empty():
                    conn = self._pool.get()
                    try:
                        conn.close()
                    except Exception as e:  # pragma: no cover - cleanup errors
                        log.warning(f"Failed to close DuckDB connection: {e}")
                self._pool = None
                self._conn = None
                self._path = None
            elif self._conn is not None:
                try:
                    self._conn.close()
                except Exception as e:  # pragma: no cover - cleanup errors
                    log.warning(f"Failed to close DuckDB connection: {e}")
                finally:
                    self._conn = None
                    self._path = None

    def clear(self) -> None:
        """
        Clear all data from the DuckDB database.

        This method removes all rows from the nodes, edges, and embeddings tables.

        Raises:
            StorageError: If the data cannot be cleared.
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        with self._lock:
            try:
                self._conn.execute("DELETE FROM nodes")
                self._conn.execute("DELETE FROM edges")
                self._conn.execute("DELETE FROM embeddings")
            except Exception as e:
                raise StorageError("Failed to clear DuckDB data", cause=e)


class KuzuStorageBackend:
    """Simple graph storage using Kuzu."""

    def __init__(self) -> None:
        self._db: kuzu.Database | None = None
        self._conn: kuzu.Connection | None = None
        self._path: str | None = None
        self._lock = Lock()

    def setup(self, db_path: str | None = None) -> None:
        try:
            import kuzu  # type: ignore
        except Exception as e:  # pragma: no cover - optional dependency
            raise StorageError("Failed to initialize Kuzu", cause=e)

        cfg = ConfigLoader().config.storage
        path = db_path or cfg.kuzu_path
        with self._lock:
            if self._conn is not None:
                return
            try:
                self._db = kuzu.Database(path)
                self._conn = kuzu.Connection(self._db)
                self._path = path
                self._conn.execute(
                    "CREATE NODE TABLE IF NOT EXISTS Claim(id STRING PRIMARY KEY, content STRING, conf DOUBLE)"
                )
            except Exception as e:
                raise StorageError("Failed to initialize Kuzu", cause=e)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute(self, query: str, params: dict[str, Any] | None = None) -> Any:
        if self._conn is None:
            raise StorageError("Kuzu connection not initialized")
        start = time.time()
        result = self._conn.execute(query, params or {})
        KUZU_QUERY_COUNTER.inc()
        KUZU_QUERY_TIME.observe(time.time() - start)
        return result

    def persist_claim(self, claim: dict[str, Any]) -> None:
        if self._conn is None:
            raise StorageError("Kuzu connection not initialized")
        self.execute(
            "MERGE (c:Claim {id: $id}) SET c.content=$content, c.conf=$conf",
            {
                "id": claim["id"],
                "content": claim.get("content", ""),
                "conf": claim.get("confidence", 0.0),
            },
        )

    def get_claim(self, claim_id: str) -> dict[str, Any]:
        if self._conn is None:
            raise StorageError("Kuzu connection not initialized")
        res = self.execute(
            "MATCH (c:Claim {id: $id}) RETURN c.content, c.conf",
            {"id": claim_id},
        )
        if res.has_next():
            row = res.get_next()
            return {"id": claim_id, "content": row[0], "confidence": row[1]}
        raise NotFoundError("Claim not found")
