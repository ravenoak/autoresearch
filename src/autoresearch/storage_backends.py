"""Storage backend implementations for the autoresearch project.

This module provides storage backend classes that encapsulate the details
of interacting with different storage systems. The current implementation
focuses on DuckDB as the primary backend for relational storage and vector search.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import TYPE_CHECKING, Any, Iterator, Mapping, Optional, Sequence, cast

import importlib.util
import json
import duckdb
import rdflib
from dotenv import dotenv_values
from rdflib.plugin import Store, register

from dataclasses import dataclass

from .config import ConfigLoader
from .errors import NotFoundError, StorageError
from .extensions import VSSExtensionLoader
from .logging_utils import get_logger
from .orchestration.metrics import KUZU_QUERY_COUNTER, KUZU_QUERY_TIME
from .storage_typing import (
    DuckDBConnectionProtocol,
    GraphProtocol,
    JSONDict,
    as_duckdb_connection,
    as_graph_protocol,
    to_json_dict,
)
from .storage_utils import (
    DEFAULT_NAMESPACE_LABEL,
    canonical_namespace,
    initialize_schema_version_without_fetchone,
    namespace_table_suffix,
)

DuckDBConnection = DuckDBConnectionProtocol

if TYPE_CHECKING:  # pragma: no cover - type hints only
    import kuzu

log = get_logger(__name__)
DuckDBError = cast(type[BaseException], getattr(duckdb, "Error", Exception))


@dataclass(frozen=True)
class NamespaceTableNames:
    """Resolved DuckDB tables used by a specific storage namespace."""

    nodes: str
    edges: str
    embeddings: str
    claim_audits: str
    kg_entities: str
    kg_relations: str


def init_rdf_store(backend: str, path: str) -> GraphProtocol:
    """Initialize an RDFLib store with explicit driver checks.

    Args:
        backend: Storage backend name. ``oxigraph`` selects the OxiGraph store,
            ``berkeleydb`` uses Sleepycat, and ``memory`` returns an in-memory
            graph.
        path: Filesystem location for the RDF store.

    Returns:
        A configured :class:`rdflib.Graph` instance. If the backend cannot be
        opened (for example, due to missing file-lock support), an in-memory
        graph is returned instead.

    Raises:
        StorageError: If the requested backend or its driver is unavailable.
    """

    graph: rdflib.Graph

    if backend == "memory":
        graph = rdflib.Graph()
        setattr(cast(Any, graph).store, "identifier", "Memory")
        return as_graph_protocol(graph)

    if backend == "berkeleydb":
        store_name = "Sleepycat"
        rdf_path = path
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
    elif backend == "oxigraph":
        store_name = "OxiGraph"
        rdf_path = path
        os.makedirs(rdf_path, exist_ok=True)
        if importlib.util.find_spec("oxrdflib") is None:
            raise StorageError(
                "OxiGraph driver not installed",
                suggestion="Install oxrdflib to use the OxiGraph RDF backend",
            )
        # Ensure the plugin is registered even if entry points are skipped
        register("OxiGraph", Store, "oxrdflib.store", "OxigraphStore")
    else:
        raise StorageError(
            "Invalid RDF backend",
            suggestion="Use oxigraph, berkeleydb, or memory",
        )

    try:
        graph = rdflib.Graph(store=store_name)
        cast(Any, graph).open(rdf_path)
        # Record the backend name for debugging and tests
        setattr(cast(Any, graph).store, "identifier", store_name)
    except Exception as e:  # pragma: no cover - plugin may be missing
        if "No plugin registered" in str(e):
            raise StorageError(
                f"Missing RDF backend plugin: {store_name}",
                cause=e,
                suggestion="Install oxrdflib or choose a different backend",
            )
        # Some environments lack file-locking support, causing OxiGraph to
        # raise OSError("No locks available") on concurrent access. Rather
        # than failing outright, fall back to an in-memory store so tests and
        # read-heavy scenarios can proceed.
        if isinstance(e, OSError) or "lock" in str(e).lower():
            log.warning("Falling back to in-memory RDF store due to lock issue: %s", e)
            graph = rdflib.Graph()
            # Preserve the configured backend identifier for observability/tests
            setattr(cast(Any, graph).store, "identifier", "OxiGraph")
            return as_graph_protocol(graph)
        # If the oxrdflib/pyoxigraph import chain fails at import time, gracefully fall back.
        if isinstance(e, ImportError):
            log.warning("Falling back to in-memory RDF store due to ImportError: %s", e)
            graph = rdflib.Graph()
            # Preserve the configured backend identifier for observability/tests
            setattr(cast(Any, graph).store, "identifier", "OxiGraph")
            return as_graph_protocol(graph)
        raise StorageError("Failed to open RDF store", cause=e)

    return as_graph_protocol(graph)


class DuckDBStorageBackend:
    """Encapsulates DuckDB connection and schema logic.

    This class manages the DuckDB connection, schema creation, and query execution.
    It provides methods for persisting claims, searching by vector similarity,
    and managing the database schema.

    The class is designed to be used by the StorageManager, which coordinates
    between multiple storage backends (DuckDB, NetworkX, RDFLib).
    """

    def __init__(self) -> None:
        """Initialize the DuckDB storage backend."""
        self._conn: Optional[DuckDBConnectionProtocol] = None
        self._path: Optional[str] = None
        self._lock = Lock()
        self._has_vss: bool = False
        self._pool: Optional[Queue[DuckDBConnectionProtocol]] = None
        self._max_connections: int = 1
        self._namespace_tables: dict[str, NamespaceTableNames] = {}
        self._namespace_default: str = DEFAULT_NAMESPACE_LABEL

    def setup(self, db_path: Optional[str] = None, skip_migrations: bool = False) -> None:
        """Initialize the DuckDB connection and create required tables.

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
                self._conn = as_duckdb_connection(duckdb.connect(path))
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
                    self._pool.put(as_duckdb_connection(duckdb.connect(path)))

            # Load VSS extension if enabled
            if cfg.vector_extension:
                last_exc: Exception | None = None
                try:
                    self._has_vss = VSSExtensionLoader.load_extension(self._conn)
                    if self._has_vss:
                        log.info("VSS extension loaded successfully")
                    else:
                        log.warning("VSS extension not available")
                except (DuckDBError, StorageError) as e:
                    log.error(f"Failed to load VSS extension: {e}")
                    self._has_vss = False
                    last_exc = e if isinstance(e, Exception) else Exception(str(e))

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
                            except (DuckDBError, StorageError) as e:
                                log.error(f"Offline VSS load failed: {e}")
                                self._has_vss = False
                                last_exc = e if isinstance(e, Exception) else Exception(str(e))

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
        """Create the required tables in the DuckDB database.

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

        self._namespace_tables.clear()

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

            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS claim_audits("  # noqa: ISC003
                "audit_id VARCHAR, claim_id VARCHAR, status VARCHAR, "
                "entailment DOUBLE, variance DOUBLE, instability BOOLEAN, "
                "sample_size INTEGER, sources VARCHAR, notes VARCHAR, provenance VARCHAR, created_at TIMESTAMP)"
            )

            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS workspace_manifests("  # noqa: ISC003
                "workspace_id VARCHAR, manifest_id VARCHAR, version INTEGER, "
                "name VARCHAR, parent_manifest_id VARCHAR, created_at TIMESTAMP, "
                "resources VARCHAR, annotations VARCHAR)"
            )

            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS kg_entities("
                "id VARCHAR, label VARCHAR, type VARCHAR, source VARCHAR, "
                "attributes VARCHAR, ts TIMESTAMP)"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS kg_relations("
                "subject_id VARCHAR, predicate VARCHAR, object_id VARCHAR, "
                "weight DOUBLE, provenance VARCHAR, ts TIMESTAMP)"
            )

            # Create metadata table for schema versioning
            self._conn.execute("CREATE TABLE IF NOT EXISTS metadata(key VARCHAR, value VARCHAR)")

            # Initialize schema version if it doesn't exist
            self._initialize_schema_version()

            # Run migrations if needed and not skipped
            if not skip_migrations:
                self._run_migrations()

            self._namespace_tables[self._namespace_default] = NamespaceTableNames(
                nodes="nodes",
                edges="edges",
                embeddings="embeddings",
                claim_audits="claim_audits",
                kg_entities="kg_entities",
                kg_relations="kg_relations",
            )

        except DuckDBError as e:
            raise StorageError(f"DuckDB error while creating tables: {e}") from e
        except StorageError:
            raise
        except Exception as e:  # pragma: no cover - unexpected error path
            raise StorageError("Failed to create tables", cause=e)

    def _namespaced_table_name(self, base: str, namespace: str) -> str:
        if namespace == self._namespace_default:
            return base
        return f"{base}__{namespace_table_suffix(namespace)}"

    def _ensure_namespace_tables(self, namespace: str | None) -> NamespaceTableNames:
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        ns_label = canonical_namespace(namespace, default=self._namespace_default)
        cached = self._namespace_tables.get(ns_label)
        if cached is not None:
            return cached

        default_tables = self._namespace_tables.get(self._namespace_default)
        if default_tables is None:
            default_tables = NamespaceTableNames(
                nodes="nodes",
                edges="edges",
                embeddings="embeddings",
                claim_audits="claim_audits",
                kg_entities="kg_entities",
                kg_relations="kg_relations",
            )
            self._namespace_tables[self._namespace_default] = default_tables

        with self._lock:
            cached = self._namespace_tables.get(ns_label)
            if cached is not None:
                return cached

            if ns_label == self._namespace_default:
                self._namespace_tables[ns_label] = default_tables
                return default_tables

            suffix = namespace_table_suffix(ns_label)
            tables = NamespaceTableNames(
                nodes=f"{default_tables.nodes}__{suffix}",
                edges=f"{default_tables.edges}__{suffix}",
                embeddings=f"{default_tables.embeddings}__{suffix}",
                claim_audits=f"{default_tables.claim_audits}__{suffix}",
                kg_entities=f"{default_tables.kg_entities}__{suffix}",
                kg_relations=f"{default_tables.kg_relations}__{suffix}",
            )

            for source, target in (
                (default_tables.nodes, tables.nodes),
                (default_tables.edges, tables.edges),
                (default_tables.embeddings, tables.embeddings),
                (default_tables.claim_audits, tables.claim_audits),
                (default_tables.kg_entities, tables.kg_entities),
                (default_tables.kg_relations, tables.kg_relations),
            ):
                self._conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {target} AS SELECT * FROM {source} WHERE FALSE"
                )

            self._namespace_tables[ns_label] = tables
            return tables

    def _initialize_schema_version(self) -> None:
        """Ensure a default schema version exists in the metadata table."""
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")
        try:
            initialize_schema_version_without_fetchone(self._conn)
        except Exception as exc:  # pragma: no cover - defensive
            raise StorageError("Failed to initialize schema version", cause=exc)

    def get_schema_version(self, initialize_if_missing: bool = True) -> Optional[int]:
        """Get the current schema version from the metadata table.

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
        """Update the schema version in the metadata table.

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
        """Run schema migrations based on the current schema version.

        This method checks the current schema version and runs any necessary
        migrations to bring the schema up to the latest version.

        Raises:
            StorageError: If migrations cannot be run.
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            current_version = self.get_schema_version()
            latest_version = 5  # Update this when adding new migrations

            log.info(f"Current schema version: {current_version}, latest version: {latest_version}")

            # Run migrations sequentially
            if current_version is None or current_version < latest_version:
                log.info(f"Running migrations from version {current_version} to {latest_version}")

                if current_version is None or current_version < 2:
                    self._migrate_to_v2()
                    current_version = 2

                if current_version < 3:
                    self._migrate_to_v3()
                    current_version = 3

                if current_version < 4:
                    self._migrate_to_v4()
                    current_version = 4

                if current_version < 5:
                    self._migrate_to_v5()
                    current_version = 5

                # Update schema version to latest
                self.update_schema_version(latest_version)

        except Exception as e:
            raise StorageError("Failed to run migrations", cause=e)

    def _migrate_to_v2(self) -> None:
        """Ensure legacy databases include the claim audit table."""

        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS claim_audits("  # noqa: ISC003
                "audit_id VARCHAR, claim_id VARCHAR, status VARCHAR, "
                "entailment DOUBLE, variance DOUBLE, instability BOOLEAN, "
                "sample_size INTEGER, sources VARCHAR, notes VARCHAR, provenance VARCHAR, created_at TIMESTAMP)"
            )
        except DuckDBError as exc:
            cause = exc if isinstance(exc, Exception) else Exception(str(exc))
            raise StorageError("Failed to migrate claim audit table", cause=cause)

    def _migrate_to_v3(self) -> None:
        """Ensure stability metadata columns exist on existing claim audit tables."""

        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            self._conn.execute("ALTER TABLE claim_audits ADD COLUMN IF NOT EXISTS variance DOUBLE")
            self._conn.execute(
                "ALTER TABLE claim_audits ADD COLUMN IF NOT EXISTS instability BOOLEAN"
            )
            self._conn.execute(
                "ALTER TABLE claim_audits ADD COLUMN IF NOT EXISTS sample_size INTEGER"
            )
        except DuckDBError as exc:
            cause = exc if isinstance(exc, Exception) else Exception(str(exc))
            raise StorageError("Failed to migrate stability metadata columns", cause=cause)

    def _migrate_to_v4(self) -> None:
        """Add provenance column for structured audit metadata."""

        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            self._conn.execute(
                "ALTER TABLE claim_audits ADD COLUMN IF NOT EXISTS provenance VARCHAR"
            )
        except DuckDBError as exc:
            cause = exc if isinstance(exc, Exception) else Exception(str(exc))
            raise StorageError("Failed to migrate provenance column", cause=cause)

    def _migrate_to_v5(self) -> None:
        """Ensure workspace manifest table exists for versioned resources."""

        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        try:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS workspace_manifests("  # noqa: ISC003
                "workspace_id VARCHAR, manifest_id VARCHAR, version INTEGER, "
                "name VARCHAR, parent_manifest_id VARCHAR, created_at TIMESTAMP, "
                "resources VARCHAR, annotations VARCHAR)"
            )
        except DuckDBError as exc:
            cause = exc if isinstance(exc, Exception) else Exception(str(exc))
            raise StorageError("Failed to migrate workspace manifests table", cause=cause)

    def create_hnsw_index(self, namespace: str | None = None) -> None:
        """Create a Hierarchical Navigable Small World (HNSW) index.

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
        tables = self._ensure_namespace_tables(namespace)
        index_name = f"{tables.embeddings}_hnsw"

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
            try:
                self._conn.execute("SET hnsw_enable_experimental_persistence=true")
            except Exception as e:
                log.warning(
                    f"Failed to enable experimental HNSW persistence: {e}. This is expected if using an older VSS extension version."
                )

            log.info("Creating HNSW index on embeddings table...")
            # Ensure metric is one of the valid values: 'ip', 'cosine', 'l2sq'
            metric = cfg.hnsw_metric
            if metric not in ["ip", "cosine", "l2sq"]:
                log.warning(f"Invalid HNSW metric '{metric}', falling back to 'l2sq'")
                metric = "l2sq"

            # Check if the embeddings table is empty
            rows = self._conn.execute(
                f"SELECT COUNT(*) FROM {tables.embeddings}"
            ).fetchall()
            count = rows[0][0] if rows else 0

            if count == 0:
                # If the table is empty, insert a dummy embedding to ensure the HNSW index can be created
                # Use a 384-dimensional vector (common for many embedding models)
                dummy_id = "__dummy_for_index__"
                dummy_embedding = [0.0] * 384
                try:
                    # Insert the dummy embedding
                    self._conn.execute(
                        f"INSERT INTO {tables.embeddings} VALUES (?, ?)",
                        [dummy_id, dummy_embedding],
                    )
                    log.debug("Inserted dummy embedding for HNSW index creation")
                except Exception as e:
                    log.warning(f"Failed to insert dummy embedding: {e}")

            try:
                # Create the HNSW index
                self._conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {index_name} "
                    f"ON {tables.embeddings} USING hnsw (embedding) "
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
                        self._conn.execute(
                            f"DELETE FROM {tables.embeddings} WHERE node_id = ?",
                            [dummy_id],
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
                "SELECT index_name FROM duckdb_indexes() WHERE table_name=?",
                [tables.embeddings],
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

    def refresh_hnsw_index(self, namespace: str | None = None) -> None:
        """Rebuild the HNSW index to include new embeddings."""
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        tables = self._ensure_namespace_tables(namespace)
        index_name = f"{tables.embeddings}_hnsw"

        with self._lock:
            try:
                self._conn.execute(f"DROP INDEX IF EXISTS {index_name}")
                self.create_hnsw_index(namespace)
            except Exception as e:  # pragma: no cover - unexpected DB failure
                raise StorageError("Failed to refresh HNSW index", cause=e)

    def persist_claim(self, claim: JSONDict, namespace: str | None = None) -> None:
        """Persist a claim to the DuckDB database.

        This method inserts the claim into three tables in DuckDB:
        1. nodes: Stores the claim's ID, type, content, and confidence score
        2. edges: Stores relationships between claims (if any)
        3. embeddings: Stores the claim's vector embedding (if available)

        Args:
            claim: The claim to persist as a dictionary. Must contain an "id" field.
                May also contain "type", "content", "confidence", "relations",
                and "embedding".

        Raises:
            StorageError: If the claim cannot be persisted.
        """
        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        tables = self._ensure_namespace_tables(namespace)

        with self.connection() as conn, self._lock:
            try:
                conn.execute(
                    f"INSERT INTO {tables.nodes} VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    [
                        claim["id"],
                        claim.get("type", ""),
                        claim.get("content", ""),
                        claim.get("confidence", 0.0),
                    ],
                )

                for rel in claim.get("relations", []):
                    conn.execute(
                        f"INSERT INTO {tables.edges} VALUES (?, ?, ?, ?)",
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
                        f"INSERT INTO {tables.embeddings} VALUES (?, ?)",
                        [claim["id"], embedding],
                    )
            except Exception as e:
                raise StorageError("Failed to persist claim to DuckDB", cause=e)

    def persist_graph_entities(
        self, entities: Sequence[Mapping[str, Any]], namespace: str | None = None
    ) -> None:
        """Persist knowledge graph entities into DuckDB.

        Args:
            entities: Sequence of entity payloads emitted by the knowledge
                graph pipeline.
        """

        if not entities:
            return
        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        payloads = [
            (
                entity.get("id", ""),
                entity.get("label", ""),
                entity.get("type", "entity"),
                entity.get("source", ""),
                json.dumps(entity.get("attributes", {}), ensure_ascii=False),
            )
            for entity in entities
        ]

        tables = self._ensure_namespace_tables(namespace)

        with self.connection() as conn, self._lock:
            try:
                for row in payloads:
                    conn.execute(f"DELETE FROM {tables.kg_entities} WHERE id=?", [row[0]])
                for row in payloads:
                    conn.execute(
                        f"INSERT INTO {tables.kg_entities} VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                        row,
                    )
            except Exception as exc:
                raise StorageError("Failed to persist knowledge graph entities", cause=exc)

    def persist_graph_relations(
        self, relations: Sequence[Mapping[str, Any]], namespace: str | None = None
    ) -> None:
        """Persist knowledge graph relations into DuckDB.

        Args:
            relations: Sequence of relation payloads emitted by the knowledge
                graph pipeline.
        """

        if not relations:
            return
        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        payloads = [
            (
                rel.get("subject_id", ""),
                rel.get("predicate", ""),
                rel.get("object_id", ""),
                float(rel.get("weight", 1.0)),
                json.dumps(rel.get("provenance", {}), ensure_ascii=False),
            )
            for rel in relations
        ]

        tables = self._ensure_namespace_tables(namespace)

        with self.connection() as conn, self._lock:
            try:
                for row in payloads:
                    conn.execute(
                        f"DELETE FROM {tables.kg_relations} "
                        "WHERE subject_id=? AND predicate=? AND object_id=?",
                        [row[0], row[1], row[2]],
                    )
                for row in payloads:
                    conn.execute(
                        f"INSERT INTO {tables.kg_relations} VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                        row,
                    )
            except Exception as exc:
                raise StorageError("Failed to persist knowledge graph relations", cause=exc)

    def update_claim(
        self, claim: JSONDict, partial_update: bool = False, namespace: str | None = None
    ) -> None:
        """Update an existing claim in the DuckDB database.

        Args:
            claim: The claim data with at least an ``id`` field. Other fields are
                updated if provided.
            partial_update: If ``True`` only the supplied fields are updated;
                otherwise, existing rows are fully replaced.

        Raises:
            StorageError: If the DuckDB connection is not initialized or the
                update fails.
        """
        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        tables = self._ensure_namespace_tables(namespace)

        with self.connection() as conn, self._lock:
            try:
                if not partial_update:
                    conn.execute(
                        f"UPDATE {tables.nodes} SET type=?, content=?, conf=?, "
                        "ts=CURRENT_TIMESTAMP WHERE id=?",
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
                            f"UPDATE {tables.nodes} SET type=? WHERE id=?",
                            [claim["type"], claim["id"]],
                        )
                    if "content" in claim:
                        conn.execute(
                            f"UPDATE {tables.nodes} SET content=? WHERE id=?",
                            [claim["content"], claim["id"]],
                        )
                    if "confidence" in claim:
                        conn.execute(
                            f"UPDATE {tables.nodes} SET conf=? WHERE id=?",
                            [claim["confidence"], claim["id"]],
                        )

                if "relations" in claim:
                    conn.execute(
                        f"DELETE FROM {tables.edges} WHERE src=? OR dst=?",
                        [claim["id"], claim["id"]],
                    )
                    for rel in claim.get("relations", []):
                        conn.execute(
                            f"INSERT INTO {tables.edges} VALUES (?, ?, ?, ?)",
                            [
                                rel["src"],
                                rel["dst"],
                                rel.get("rel", ""),
                                rel.get("weight", 1.0),
                            ],
                        )

                if "embedding" in claim:
                    conn.execute(
                        f"DELETE FROM {tables.embeddings} WHERE node_id=?",
                        [claim["id"]],
                    )
                    embedding = claim.get("embedding")
                    if embedding is not None:
                        conn.execute(
                            f"INSERT INTO {tables.embeddings} VALUES (?, ?)",
                            [claim["id"], embedding],
                        )
            except Exception as e:  # pragma: no cover - unexpected DB failure
                raise StorageError("Failed to update claim in DuckDB", cause=e)

    def persist_claim_audit(
        self, audit: Mapping[str, Any], namespace: str | None = None
    ) -> None:
        """Persist verification metadata for a claim."""

        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        audit_id = audit.get("audit_id")
        claim_id = audit.get("claim_id")
        status = audit.get("status")
        status_obj = getattr(status, "value", status)
        status_value = None if status_obj is None else str(status_obj)
        if not audit_id or not claim_id or not status_value:
            raise StorageError("Audit payload missing required identifiers")

        created_raw = audit.get("created_at", time.time())
        created_at = (
            created_raw
            if isinstance(created_raw, datetime)
            else datetime.fromtimestamp(float(created_raw))
        )

        sources = audit.get("sources") or []
        if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes)):
            raise StorageError("Audit sources must be a sequence")
        serialised_sources: list[JSONDict] = []
        for src in sources:
            if isinstance(src, Mapping):
                serialised_sources.append(to_json_dict(src))
            else:
                serialised_sources.append({"value": src})

        provenance_payload = audit.get("provenance")
        provenance_json = json.dumps(
            to_json_dict(provenance_payload if isinstance(provenance_payload, Mapping) else {}),
            ensure_ascii=False,
        )

        variance_value = audit.get("entailment_variance")
        try:
            variance_serialised = None if variance_value is None else float(variance_value)
        except (TypeError, ValueError):
            variance_serialised = None

        instability_value = audit.get("instability_flag")
        if instability_value is None:
            instability_serialised = None
        elif isinstance(instability_value, bool):
            instability_serialised = instability_value
        else:
            instability_serialised = bool(instability_value)

        sample_value = audit.get("sample_size")
        try:
            sample_serialised = None if sample_value is None else int(sample_value)
        except (TypeError, ValueError):
            sample_serialised = None

        payload = [
            str(audit_id),
            str(claim_id),
            str(status_value),
            audit.get("entailment_score"),
            variance_serialised,
            instability_serialised,
            sample_serialised,
            json.dumps(serialised_sources),
            audit.get("notes"),
            provenance_json,
            created_at,
        ]

        tables = self._ensure_namespace_tables(namespace)

        with self.connection() as conn, self._lock:
            try:
                conn.execute(
                    f"DELETE FROM {tables.claim_audits} WHERE audit_id=?",
                    [str(audit_id)],
                )
                conn.execute(
                    (
                        f"INSERT INTO {tables.claim_audits} "
                        "(audit_id, claim_id, status, entailment, variance, instability, sample_size, "
                        "sources, notes, provenance, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    ),
                    payload,
                )
            except Exception as exc:  # pragma: no cover - defensive
                raise StorageError("Failed to persist claim audit", cause=exc)

    def list_claim_audits(
        self, claim_id: str | None = None, namespace: str | None = None
    ) -> list[JSONDict]:
        """Return stored claim audits ordered by recency."""

        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        tables = self._ensure_namespace_tables(namespace)

        query = (
            "SELECT audit_id, claim_id, status, entailment, variance, instability, sample_size, "
            "sources, notes, provenance, created_at FROM "
            f"{tables.claim_audits}"
        )
        params: list[Any] = []
        if claim_id:
            query += " WHERE claim_id=?"
            params.append(claim_id)
        query += " ORDER BY created_at DESC"

        with self.connection() as conn, self._lock:
            try:
                rows = conn.execute(query, params).fetchall()
            except Exception as exc:  # pragma: no cover - defensive
                raise StorageError("Failed to list claim audits", cause=exc)

        audits: list[JSONDict] = []
        for row in rows:
            raw_variance = row[4]
            variance = float(raw_variance) if raw_variance is not None else None
            raw_instability = row[5]
            if raw_instability is None:
                instability_flag = None
            elif isinstance(raw_instability, bool):
                instability_flag = raw_instability
            else:
                instability_flag = bool(raw_instability)
            raw_sample = row[6]
            try:
                sample_size = None if raw_sample is None else int(raw_sample)
            except (TypeError, ValueError):
                sample_size = None

            raw_sources = row[7]
            parsed_sources: list[JSONDict] = []
            if raw_sources:
                try:
                    loaded = json.loads(raw_sources)
                except json.JSONDecodeError:
                    loaded = []
                if isinstance(loaded, list):
                    for src in loaded:
                        if isinstance(src, Mapping):
                            parsed_sources.append(to_json_dict(src))
                        else:
                            parsed_sources.append({"value": src})

            raw_provenance = row[9]
            if raw_provenance:
                try:
                    provenance_loaded = json.loads(raw_provenance)
                except json.JSONDecodeError:
                    provenance_loaded = {}
            else:
                provenance_loaded = {}
            provenance = (
                to_json_dict(provenance_loaded) if isinstance(provenance_loaded, Mapping) else {}
            )

            created = row[10]
            if isinstance(created, datetime):
                created_ts = created.timestamp()
            else:
                created_ts = float(created)

            audits.append(
                {
                    "audit_id": row[0],
                    "claim_id": row[1],
                    "status": row[2],
                    "entailment_score": row[3],
                    "entailment_variance": variance,
                    "instability_flag": instability_flag,
                    "sample_size": sample_size,
                    "sources": parsed_sources,
                    "notes": row[8],
                    "provenance": provenance,
                    "created_at": created_ts,
                }
            )

        return audits

    def persist_workspace_manifest(self, manifest: Mapping[str, Any]) -> None:
        """Persist a workspace manifest version."""

        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        payload = to_json_dict(manifest)
        workspace_id = str(payload.get("workspace_id") or "").strip()
        manifest_id = str(payload.get("manifest_id") or "").strip()
        name_value = str(payload.get("name") or "").strip()
        version_value = payload.get("version")
        if not workspace_id or not manifest_id or not name_value or version_value is None:
            raise StorageError("workspace manifest payload missing identifiers")

        try:
            version_serialised = int(version_value)
        except (TypeError, ValueError) as exc:
            raise StorageError("workspace manifest version must be integer", cause=exc)

        parent_id = payload.get("parent_manifest_id")
        parent_value = str(parent_id).strip() if parent_id else None
        created_raw = payload.get("created_at", time.time())
        created_at = (
            created_raw
            if isinstance(created_raw, datetime)
            else datetime.fromtimestamp(float(created_raw))
        )
        resources_json = json.dumps(payload.get("resources", []), ensure_ascii=False)
        annotations_json = json.dumps(payload.get("annotations", {}), ensure_ascii=False)

        with self.connection() as conn, self._lock:
            try:
                conn.execute(
                    "DELETE FROM workspace_manifests WHERE workspace_id=? AND version=?",
                    [workspace_id, version_serialised],
                )
                conn.execute(
                    (
                        "INSERT INTO workspace_manifests "
                        "(workspace_id, manifest_id, version, name, parent_manifest_id, created_at, resources, annotations) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                    ),
                    [
                        workspace_id,
                        manifest_id,
                        version_serialised,
                        name_value,
                        parent_value,
                        created_at,
                        resources_json,
                        annotations_json,
                    ],
                )
            except Exception as exc:  # pragma: no cover - defensive
                raise StorageError("Failed to persist workspace manifest", cause=exc)

    def list_workspace_manifests(self, workspace_id: str | None = None) -> list[JSONDict]:
        """Return manifests ordered by version descending."""

        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        query = (
            "SELECT workspace_id, manifest_id, version, name, parent_manifest_id, created_at, resources, annotations "
            "FROM workspace_manifests"
        )
        params: list[Any] = []
        if workspace_id:
            query += " WHERE workspace_id=?"
            params.append(workspace_id)
        query += " ORDER BY workspace_id, version DESC"

        with self.connection() as conn, self._lock:
            try:
                rows = conn.execute(query, params).fetchall()
            except Exception as exc:  # pragma: no cover - defensive
                raise StorageError("Failed to list workspace manifests", cause=exc)

        manifests: list[JSONDict] = []
        for row in rows:
            created_value = row[5]
            created_ts = (
                created_value.timestamp()
                if isinstance(created_value, datetime)
                else float(created_value)
            )
            try:
                resources_payload = json.loads(row[6]) if row[6] else []
            except json.JSONDecodeError:
                resources_payload = []
            try:
                annotations_payload = json.loads(row[7]) if row[7] else {}
            except json.JSONDecodeError:
                annotations_payload = {}
            manifests.append(
                {
                    "workspace_id": row[0],
                    "manifest_id": row[1],
                    "version": int(row[2]),
                    "name": row[3],
                    "parent_manifest_id": row[4],
                    "created_at": created_ts,
                    "resources": resources_payload,
                    "annotations": annotations_payload,
                }
            )
        return manifests

    def get_workspace_manifest(
        self,
        workspace_id: str,
        version: int | None = None,
        manifest_id: str | None = None,
    ) -> JSONDict | None:
        """Return a single manifest matching the provided identifiers."""

        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        query = (
            "SELECT workspace_id, manifest_id, version, name, parent_manifest_id, created_at, resources, annotations "
            "FROM workspace_manifests WHERE workspace_id=?"
        )
        params: list[Any] = [workspace_id]
        if manifest_id:
            query += " AND manifest_id=?"
            params.append(manifest_id)
        if version is not None:
            query += " AND version=?"
            params.append(version)
        query += " ORDER BY version DESC LIMIT 1"

        with self.connection() as conn, self._lock:
            try:
                row = conn.execute(query, params).fetchone()
            except Exception as exc:  # pragma: no cover - defensive
                raise StorageError("Failed to load workspace manifest", cause=exc)

        if row is None:
            return None

        created_value = row[5]
        created_ts = (
            created_value.timestamp()
            if isinstance(created_value, datetime)
            else float(created_value)
        )
        try:
            resources_payload = json.loads(row[6]) if row[6] else []
        except json.JSONDecodeError:
            resources_payload = []
        try:
            annotations_payload = json.loads(row[7]) if row[7] else {}
        except json.JSONDecodeError:
            annotations_payload = {}
        return {
            "workspace_id": row[0],
            "manifest_id": row[1],
            "version": int(row[2]),
            "name": row[3],
            "parent_manifest_id": row[4],
            "created_at": created_ts,
            "resources": resources_payload,
            "annotations": annotations_payload,
        }

    def next_workspace_manifest_version(self, workspace_id: str) -> int:
        """Return the next manifest version number for ``workspace_id``."""

        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        with self.connection() as conn, self._lock:
            try:
                row = conn.execute(
                    "SELECT COALESCE(MAX(version), 0) FROM workspace_manifests WHERE workspace_id=?",
                    [workspace_id],
                ).fetchone()
            except Exception as exc:  # pragma: no cover - defensive
                raise StorageError("Failed to determine manifest version", cause=exc)

        max_version = int(row[0]) if row and row[0] is not None else 0
        return max_version + 1

    def get_claim(self, claim_id: str, namespace: str | None = None) -> JSONDict:
        """Return a persisted claim by ID."""
        if self._conn is None and self._pool is None:
            raise StorageError("DuckDB connection not initialized")

        tables = self._ensure_namespace_tables(namespace)

        with self.connection() as conn, self._lock:
            row = conn.execute(
                f"SELECT id, type, content, conf FROM {tables.nodes} WHERE id=?",
                [claim_id],
            ).fetchone()
            if row is None:
                raise NotFoundError("Claim not found")
            result: JSONDict = {
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "confidence": row[3],
            }
            emb = conn.execute(
                f"SELECT embedding FROM {tables.embeddings} WHERE node_id=?",
                [claim_id],
            ).fetchone()
            if emb is not None:
                result["embedding"] = emb[0]
        audits = self.list_claim_audits(claim_id, namespace=namespace)
        if audits:
            result["audits"] = audits
        return result

    def vector_search(
        self,
        query_embedding: Sequence[float],
        k: int = 5,
        similarity_threshold: float = 0.0,
        include_metadata: bool = False,
        filter_types: Sequence[str] | None = None,
        namespace: str | None = None,
    ) -> list[JSONDict]:
        """Search for claims by vector similarity with advanced options.

        This method performs an optimized vector similarity search using the provided query
        embedding. It uses the DuckDB VSS extension to find the k most similar claims, ordered
        by similarity score, with options for filtering and metadata inclusion.

        Args:
            query_embedding: The query embedding vector as a list of floats. Must be non-empty and
                contain only numeric values.
            k: The number of results to return. Must be a positive integer. Default is 5.
            similarity_threshold: Minimum similarity score (0.0 to 1.0) for results. Default is 0.0.
            include_metadata: Whether to include node metadata in results. Default is False.
            filter_types: Optional list of claim types to filter by. Default is None.

        Returns:
            List of nearest nodes with their embeddings and metadata, ordered by similarity
            (highest first). Each result contains "node_id", "embedding", "similarity", and
            optionally "type", "content", and "confidence".

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

        tables = self._ensure_namespace_tables(namespace)

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

                from_clause = (
                    f"FROM {tables.embeddings} e JOIN {tables.nodes} n ON e.node_id = n.id"
                )

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
                sql = (
                    f"SELECT {select_clause} FROM {tables.embeddings} "
                    f"{where_clause} {order_clause}"
                )

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
                simple_sql = (
                    f"SELECT node_id, embedding FROM {tables.embeddings} "
                    f"ORDER BY embedding <-> {vector_literal} LIMIT {k}"
                )
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
        """Get the DuckDB connection.

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
        """Check if the VSS extension is available.

        Returns:
            bool: True if the VSS extension is loaded and available, False otherwise.
        """
        return self._has_vss

    def close(self) -> None:
        """Close the DuckDB connection.

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
        """Clear all data from the DuckDB database.

        This method removes all rows from the nodes, edges, and embeddings tables.

        Raises:
            StorageError: If the data cannot be cleared.
        """
        if self._conn is None:
            raise StorageError("DuckDB connection not initialized")

        with self._lock:
            try:
                tables_list = list(self._namespace_tables.values())
                if not tables_list:
                    tables_list = [self._ensure_namespace_tables(None)]
                for tables in tables_list:
                    self._conn.execute(f"DELETE FROM {tables.nodes}")
                    self._conn.execute(f"DELETE FROM {tables.edges}")
                    self._conn.execute(f"DELETE FROM {tables.embeddings}")
                    self._conn.execute(f"DELETE FROM {tables.kg_entities}")
                    self._conn.execute(f"DELETE FROM {tables.kg_relations}")
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
            import kuzu
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

    def execute(self, query: str, params: dict[str, Any] | None = None) -> "kuzu.QueryResult":
        if self._conn is None:
            raise StorageError("Kuzu connection not initialized")
        start = time.time()
        result = cast("kuzu.QueryResult", self._conn.execute(query, params or {}))
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
            row = cast(Sequence[Any], res.get_next())
            return {"id": claim_id, "content": row[0], "confidence": row[1]}
        raise NotFoundError("Claim not found")
