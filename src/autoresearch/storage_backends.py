"""
Storage backend implementations for the autoresearch project.

This module provides storage backend classes that encapsulate the details
of interacting with different storage systems. The current implementation
focuses on DuckDB as the primary backend for relational storage and vector search.
"""

import os
from threading import Lock
from typing import Any, Optional, List, Dict

import duckdb

from .config import ConfigLoader
from .errors import StorageError, NotFoundError
from .extensions import VSSExtensionLoader
from .logging_utils import get_logger

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
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
        self._path: Optional[str] = None
        self._lock = Lock()
        self._has_vss: bool = False

    def setup(
        self, db_path: Optional[str] = None, skip_migrations: bool = False
    ) -> None:
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
                else cfg.duckdb.path
                if hasattr(cfg, "duckdb") and hasattr(cfg.duckdb, "path")
                else os.getenv("DUCKDB_PATH", "kg.duckdb")
            )
            self._path = path

            try:
                self._conn = duckdb.connect(path)
            except Exception as e:
                log.error(f"Failed to connect to DuckDB database: {e}")
                self._conn = None
                raise StorageError("Failed to connect to DuckDB database", cause=e)

            # Load VSS extension if enabled
            if cfg.vector_extension:
                try:
                    self._has_vss = VSSExtensionLoader.load_extension(self._conn)
                    if self._has_vss:
                        log.info("VSS extension loaded successfully")
                    else:
                        log.warning("VSS extension not available")
                except Exception as e:
                    log.error(f"Failed to load VSS extension: {e}")
                    self._has_vss = False
                    # In test environments, we don't want to fail if the VSS extension is not available
                    # Only raise in non-test environments or if explicitly configured to fail
                    if (
                        os.getenv("AUTORESEARCH_STRICT_EXTENSIONS", "").lower()
                        == "true"
                    ):
                        raise StorageError("Failed to load VSS extension", cause=e)

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
                "CREATE TABLE IF NOT EXISTS embeddings("
                "node_id VARCHAR, embedding FLOAT[384])"
            )

            # Create metadata table for schema versioning
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS metadata(key VARCHAR, value VARCHAR)"
            )

            # Initialize schema version if it doesn't exist
            self._initialize_schema_version()

            # Run migrations if needed and not skipped
            if not skip_migrations:
                self._run_migrations()

        except Exception as e:
            raise StorageError("Failed to create tables", cause=e)

    def _initialize_schema_version(self) -> None:
        """
        Initialize the schema version in the metadata table if it doesn't exist.

        This method checks if a schema_version entry exists in the metadata table,
        and if not, it inserts a default value of "1".

        Raises:
            StorageError: If the schema version cannot be initialized.
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            # Check if schema_version exists
            result = self._conn.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()

            # If not, initialize it to version 1
            if result is None:
                log.info("Initializing schema version to 1")
                self._conn.execute(
                    "INSERT INTO metadata (key, value) VALUES ('schema_version', '1')"
                )
        except Exception as e:
            raise StorageError("Failed to initialize schema version", cause=e)

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
            result = self._conn.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()

            if result is None:
                if initialize_if_missing:
                    # This should not happen as _initialize_schema_version should have been called
                    log.warning(
                        "Schema version not found in metadata table, initializing to 1"
                    )
                    self._initialize_schema_version()
                    return 1
                else:
                    return None

            return int(result[0])
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

            log.info(
                f"Current schema version: {current_version}, latest version: {latest_version}"
            )

            # Run migrations sequentially
            if current_version is None or current_version < latest_version:
                log.info(
                    f"Running migrations from version {current_version} to {latest_version}"
                )

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
            count = self._conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]

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

                # If we inserted a dummy embedding, remove it now
                if count == 0:
                    try:
                        self._conn.execute(
                            "DELETE FROM embeddings WHERE node_id = ?", [dummy_id]
                        )
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
                log.warning(
                    "HNSW index creation appeared to succeed, but no index was found"
                )
            else:
                log.info(f"Verified index creation: {indexes}")

        except Exception as e:
            log.error(f"Failed to create HNSW index: {e}")
            # In test environments, we don't want to fail if the HNSW index creation fails
            # Only raise in non-test environments or if explicitly configured to fail
            if os.getenv("AUTORESEARCH_STRICT_EXTENSIONS", "").lower() == "true":
                raise StorageError("Failed to create HNSW index", cause=e)

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
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        with self._lock:
            try:
                # Insert node row
                self._conn.execute(
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
                    self._conn.execute(
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
                    self._conn.execute(
                        "INSERT INTO embeddings VALUES (?, ?)",
                        [claim["id"], embedding],
                    )
            except Exception as e:
                raise StorageError("Failed to persist claim to DuckDB", cause=e)

    def vector_search(
        self, query_embedding: List[float], k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for claims by vector similarity.

        This method performs a vector similarity search using the provided query embedding.
        It uses the DuckDB VSS extension to find the k most similar claims, ordered by
        similarity score.

        Args:
            query_embedding: The query embedding vector as a list of floats.
                           Must be non-empty and contain only numeric values.
            k: The number of results to return. Must be a positive integer.
               Default is 5.

        Returns:
            List of nearest nodes with their embeddings, ordered by similarity (highest first).
            Each result contains 'node_id' and 'embedding'.

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

        try:
            # Set search parameters
            try:
                self._conn.execute(f"SET hnsw_ef_search={cfg.vector_nprobe}")
            except Exception as e:
                log.debug(f"Failed to set hnsw_ef_search: {e}, continuing with default")

            # Format query and execute search
            vector_literal = f"[{', '.join(str(x) for x in query_embedding)}]"
            sql = (
                "SELECT node_id, embedding FROM embeddings "
                f"ORDER BY embedding <-> {vector_literal} LIMIT {k}"
            )
            rows = self._conn.execute(sql).fetchall()

            # Format results
            return [{"node_id": r[0], "embedding": r[1]} for r in rows]
        except Exception as e:
            log.error(f"Vector search failed: {e}")
            raise StorageError(
                "Vector search failed",
                cause=e,
                suggestion="Check that the VSS extension is properly installed and that embeddings exist in the database",
            )

    def get_connection(self) -> duckdb.DuckDBPyConnection:
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
            if self._conn is not None:
                try:
                    self._conn.close()
                    self._conn = None
                    self._path = None
                except Exception as e:
                    log.warning(f"Failed to close DuckDB connection: {e}")
                    # We don't raise here as this is cleanup code

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
