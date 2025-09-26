"""
Hybrid Distributed Knowledge Graph (DKG) persistence system.

This module provides a storage system that combines three backends:
1. NetworkX: For in-memory graph storage and traversal
2. DuckDB: For relational storage and vector search
3. RDFLib: For semantic graph storage and SPARQL queries

The storage system supports claim persistence, vector search, and automatic
resource management with configurable eviction policies. See
``docs/algorithms/cache_eviction.md`` for proofs of the LRU policy.

Note on VSS Extension:
The vector search functionality requires the DuckDB VSS extension.
If the extension is not available, the system continues to operate but
vector search calls return empty results. Claims and embeddings are still
stored in the database.
The system attempts to install and load the VSS extension automatically
if it's enabled in the configuration.
"""

from __future__ import annotations

import importlib.util
import json
import os
import time
from collections import OrderedDict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from threading import RLock
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    cast,
)
from uuid import uuid4

import networkx as nx
import rdflib

from .config import ConfigLoader, StorageConfig
from .errors import ConfigError, NotFoundError, StorageError
from .kg_reasoning import run_ontology_reasoner
from .logging_utils import get_logger
from .orchestration.metrics import EVICTION_COUNTER
from .storage_backends import DuckDBStorageBackend, init_rdf_store

if TYPE_CHECKING:  # pragma: no cover
    from .storage_backends import KuzuStorageBackend

# Typed reference to the optional Kuzu backend.
KuzuBackend: type[KuzuStorageBackend] | None = None

# Determine availability of the optional Kuzu dependency without importing it
try:  # pragma: no cover - optional dependency
    _has_kuzu = importlib.util.find_spec("kuzu") is not None
except Exception:  # pragma: no cover - defensive
    _has_kuzu = False

if _has_kuzu:  # pragma: no cover - optional dependency
    from .storage_backends import KuzuStorageBackend as _KuzuStorageBackend

    KuzuBackend = cast(type[_KuzuStorageBackend], _KuzuStorageBackend)

# Use "Any" for DuckDB connections due to incomplete upstream type hints.
DuckDBConnection = Any


@dataclass
class StorageContext:
    """Container for storage backend instances."""

    graph: Optional[nx.DiGraph[Any]] = None
    db_backend: Optional[DuckDBStorageBackend] = None
    rdf_store: Optional[rdflib.Graph] = None
    config_fingerprint: Optional[str] = None


# Container for stateful components
@dataclass
class StorageState:
    """Holds runtime storage state for injection.

    The ``lru`` field is an :class:`collections.OrderedDict` whose ordering is
    used to determine eviction order.
    """

    context: StorageContext = field(default_factory=StorageContext)
    # Use a monotonically increasing counter rather than wall-clock timestamps
    # for LRU bookkeeping. Relying on ``time.time`` can yield identical values
    # when operations occur in rapid succession which then makes eviction order
    # dependent on dict insertion ordering. A simple counter guarantees a stable
    # and deterministic order across runs.
    lru: "OrderedDict[str, int]" = field(default_factory=OrderedDict)
    lru_counter: int = 0
    lock: RLock = field(default_factory=RLock)
    baseline_mb: float = 0.0


_default_state = StorageState()
_kuzu_backend: KuzuStorageBackend | None = None
log = get_logger(__name__)

# Optional injection point for tests
_delegate: type["StorageManager"] | None = None
# Optional queue for distributed persistence
_message_queue: Any | None = None

_cached_config: StorageConfig | None = None

# At least two claims should remain resident when eviction falls back to
# deterministic limits derived from RAM budgets. This guards against noisy
# metrics (e.g., when the VSS extension toggles persistence settings) from
# evicting the entire working set.
_MIN_DETERMINISTIC_SURVIVORS = 2


class ClaimAuditStatus(StrEnum):
    """Verification label assigned to a claim."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    NEEDS_REVIEW = "needs_review"

    @classmethod
    def from_entailment(cls, score: float | None) -> "ClaimAuditStatus":
        """Map an entailment score onto a FEVER-style status label.

        Args:
            score: Normalised entailment score between 0 and 1.

        Returns:
            ClaimAuditStatus: The corresponding verification label.
        """

        if score is None:
            return cls.NEEDS_REVIEW
        if score >= 0.6:
            return cls.SUPPORTED
        if score <= 0.3:
            return cls.UNSUPPORTED
        return cls.NEEDS_REVIEW


@dataclass(slots=True)
class ClaimAuditRecord:
    """Structured verification metadata stored alongside claims."""

    claim_id: str
    status: ClaimAuditStatus
    entailment_score: float | None = None
    sources: list[dict[str, Any]] = field(default_factory=list)
    notes: str | None = None
    audit_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: float = field(default_factory=time.time)

    def to_payload(self) -> dict[str, Any]:
        """Serialise the record into a JSON-compatible payload."""

        return {
            "audit_id": self.audit_id,
            "claim_id": self.claim_id,
            "status": self.status.value,
            "entailment_score": self.entailment_score,
            "sources": self.sources,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ClaimAuditRecord":
        """Create a record from a dictionary payload."""

        status_value = payload.get("status", ClaimAuditStatus.NEEDS_REVIEW)
        if isinstance(status_value, ClaimAuditStatus):
            status = status_value
        else:
            try:
                status = ClaimAuditStatus(str(status_value))
            except ValueError as exc:  # pragma: no cover - defensive
                raise StorageError("Invalid claim audit status") from exc
        sources = payload.get("sources") or []
        if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes)):
            raise StorageError("sources must be a sequence of mappings")
        serialised_sources: list[dict[str, Any]] = []
        for src in sources:
            if isinstance(src, Mapping):
                serialised_sources.append(dict(src))
            else:
                raise StorageError("each source must be a mapping")
        created_at = float(payload.get("created_at", time.time()))
        audit_id = payload.get("audit_id") or str(uuid4())
        claim_id = str(payload.get("claim_id", ""))
        if not claim_id:
            raise StorageError("claim_id is required for claim audit records")
        return cls(
            claim_id=claim_id,
            status=status,
            entailment_score=payload.get("entailment_score"),
            sources=serialised_sources,
            notes=payload.get("notes"),
            audit_id=audit_id,
            created_at=created_at,
        )


def _process_ram_mb() -> float:
    """Return the process resident set size in megabytes."""
    try:
        import psutil

        mem = psutil.Process(os.getpid()).memory_info().rss
        return float(mem) / (1024**2)
    except Exception as e:  # pragma: no cover - optional dependency
        log.debug(f"Failed to get memory usage with psutil: {e}")
        try:
            import resource
            import sys

            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform == "darwin":
                return usage / (1024**2)
            return usage / 1024
        except Exception as e2:
            log.warning(f"Failed to get memory usage: {e2}")
            return 0.0


def _get_config() -> StorageConfig:
    """Return cached storage configuration."""
    global _cached_config
    if _cached_config is None:
        try:
            config = ConfigLoader().config
        except ConfigError:
            _cached_config = StorageConfig()
        else:
            storage_cfg = getattr(config, "storage", None)
            if isinstance(storage_cfg, StorageConfig):
                _cached_config = storage_cfg
            elif storage_cfg is None:
                _cached_config = StorageConfig()
            else:
                try:
                    data = storage_cfg
                    if not isinstance(storage_cfg, dict):
                        try:
                            data = vars(storage_cfg)
                        except Exception:
                            pass
                    _cached_config = StorageConfig.model_validate(data)
                except Exception:  # pragma: no cover - defensive
                    log.debug(
                        "Storage configuration missing or invalid; using defaults",
                        exc_info=True,
                    )
                    _cached_config = StorageConfig()
    return _cached_config


def _fingerprint_config(cfg: StorageConfig) -> str:
    """Return a stable fingerprint for the active storage configuration."""

    return json.dumps(
        cfg.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )


def _reset_context(ctx: StorageContext) -> None:
    """Close existing storage resources prior to reinitialization."""

    global _kuzu_backend

    if ctx.db_backend is not None:
        try:
            ctx.db_backend.close()
        except Exception as exc:  # pragma: no cover - defensive cleanup
            log.warning("Failed to close DuckDB backend during reinit: %s", exc)
        ctx.db_backend = None

    if ctx.rdf_store is not None:
        try:
            ctx.rdf_store.close()
        except Exception as exc:  # pragma: no cover - defensive cleanup
            log.warning("Failed to close RDF store during reinit: %s", exc)
        ctx.rdf_store = None

    if _kuzu_backend is not None:
        try:
            _kuzu_backend.close()
        except Exception as exc:  # pragma: no cover - optional dependency
            log.warning("Failed to close Kuzu backend during reinit: %s", exc)
        _kuzu_backend = None

    ctx.graph = None
    ctx.config_fingerprint = None


def set_message_queue(queue: Any | None) -> None:
    """Configure a message queue for distributed persistence."""
    global _message_queue
    _message_queue = queue


def set_delegate(delegate: type["StorageManager"] | None) -> None:
    """Replace StorageManager implementation globally."""
    global _delegate
    _delegate = delegate


def get_delegate() -> type["StorageManager"] | None:
    """Return the injected StorageManager class if any."""
    return _delegate


def setup(
    db_path: Optional[str] = None,
    context: StorageContext | None = None,
    state: StorageState | None = None,
) -> None:
    """Initialise storage components if not already initialised."""
    global _kuzu_backend
    st = state or _default_state
    ctx = context or st.context
    with st.lock:
        if st.baseline_mb == 0.0:
            st.baseline_mb = _process_ram_mb()

        global _cached_config
        _cached_config = None
        cfg = _get_config()
        fingerprint = _fingerprint_config(cfg)

        backend = ctx.db_backend
        backend_ready = (
            backend is not None
            and backend.get_connection() is not None
            and ctx.rdf_store is not None
        )

        if backend_ready and ctx.config_fingerprint == fingerprint:
            st.context = ctx
            return

        if backend_ready and ctx.config_fingerprint != fingerprint:
            _reset_context(ctx)

        ctx.graph = nx.DiGraph()

        # Initialize DuckDB backend with graceful fallback when VSS is missing
        ctx.db_backend = DuckDBStorageBackend()
        try:
            ctx.db_backend.setup(db_path)
        except StorageError as exc:
            log.warning("DuckDB setup failed (%s); retrying without vector search", exc)
            cfg.vector_extension = False
            ctx.db_backend = DuckDBStorageBackend()
            ctx.db_backend.setup(db_path)

        # Initialize Kuzu backend when enabled
        use_kuzu = getattr(cfg, "use_kuzu", False)
        if use_kuzu and KuzuBackend is None:
            log.warning("Kuzu backend requested but not available")
            cfg.use_kuzu = False
        elif use_kuzu and KuzuBackend is not None:
            _kuzu_backend = KuzuBackend()
            kuzu_path = getattr(cfg, "kuzu_path", StorageConfig().kuzu_path)
            _kuzu_backend.setup(kuzu_path)

        # Initialize RDF store; propagate errors so callers can handle misconfiguration explicitly.
        ctx.rdf_store = init_rdf_store(cfg.rdf_backend, cfg.rdf_path)
        ctx.config_fingerprint = fingerprint
    st.context = ctx


def initialize_storage(
    db_path: str | None = None,
    context: StorageContext | None = None,
    state: StorageState | None = None,
) -> StorageContext:
    """Initialize storage and ensure DuckDB tables exist.

    ``setup`` initializes connections while ``_create_tables`` runs on every
    call to guarantee that required tables exist, even when a previous run has
    already created them. DuckDB's in-memory databases start empty each time,
    so this extra invocation keeps behaviour consistent across sessions.

    Args:
        db_path: Optional path to the DuckDB database. ``:memory:`` creates
            an ephemeral database.
        context: Optional :class:`StorageContext` to initialize.
        state: Optional :class:`StorageState` providing runtime storage
            state.

    Returns:
        StorageContext: The initialized storage context.

    Raises:
        StorageError: If the DuckDB backend is missing after initialization.
    """

    st = state or _default_state
    ctx = context or st.context

    with st.lock:
        backend = ctx.db_backend
        backend_ready = (
            backend is not None
            and backend.get_connection() is not None
            and ctx.rdf_store is not None
        )
        if not backend_ready:
            setup(db_path, ctx, st)

        backend = ctx.db_backend
        if backend is None:
            raise StorageError("DuckDB backend not initialized")

        # Always run table creation to guard against missing schema components.
        backend.get_connection()
        backend._create_tables(skip_migrations=True)

    return ctx


def teardown(
    remove_db: bool = False,
    context: StorageContext | None = None,
    state: StorageState | None = None,
) -> None:
    """Close connections and optionally remove the DuckDB file.

    This method closes all storage connections (DuckDB, RDF) and optionally
    removes the database files. It handles exceptions gracefully to ensure
    that cleanup always completes, even if errors occur during closing.

    Args:
        remove_db: If True, also removes the database files from disk.
                  Default is False.
    """
    global _cached_config
    global _kuzu_backend
    st = state or _default_state
    ctx = context or st.context
    with st.lock:
        # Close DuckDB connection
        if ctx.db_backend is not None:
            try:
                # Get the path before closing the connection
                db_path = None
                try:
                    db_path = ctx.db_backend._path
                except Exception as e:
                    log.debug(f"Could not determine DuckDB path for cleanup: {e}")

                # Close the connection
                ctx.db_backend.close()

                # Remove the database file if requested
                if remove_db and db_path and os.path.exists(db_path):
                    os.remove(db_path)
            except Exception as e:  # pragma: no cover - optional close
                log.warning(f"Failed to close DuckDB connection: {e}")
                # We don't raise here as this is cleanup code

        # Close RDF store
        if ctx.rdf_store is not None:
            try:
                ctx.rdf_store.close()
            except Exception as e:  # pragma: no cover - optional close
                log.warning(f"Failed to close RDF store: {e}")
                # We don't raise here as this is cleanup code

        # Remove RDF store files if requested
        cfg = _get_config()
        if remove_db and os.path.exists(cfg.rdf_path):
            if os.path.isdir(cfg.rdf_path):
                import shutil

                shutil.rmtree(cfg.rdf_path, ignore_errors=True)
            else:
                os.remove(cfg.rdf_path)

        if _kuzu_backend is not None:
            try:
                _kuzu_backend.close()
                if remove_db and _kuzu_backend._path and os.path.exists(_kuzu_backend._path):
                    os.remove(_kuzu_backend._path)
            except Exception as e:
                log.warning(f"Failed to close Kuzu connection: {e}")

        # Reset global variables
        ctx.graph = None
        ctx.db_backend = None
        _kuzu_backend = None
        ctx.rdf_store = None
        ctx.config_fingerprint = None
        if st.lru is not None:
            st.lru.clear()
        # Clear access frequency tracking to avoid stale state between runs
        try:
            StorageManager._access_frequency.clear()
        except NameError:  # pragma: no cover - StorageManager not yet defined
            pass
        st.context = ctx
        _cached_config = None


class StorageManagerMeta(type):
    state: StorageState = _default_state

    @property
    def context(cls) -> StorageContext:
        return cls.state.context

    @context.setter
    def context(cls, value: StorageContext) -> None:
        cls.state.context = value


class StorageManager(metaclass=StorageManagerMeta):
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

    _access_frequency: ClassVar[dict[str, int]] = {}
    _last_adaptive_policy: ClassVar[str] = "lru"

    @staticmethod
    def setup(
        db_path: Optional[str] = None,
        context: StorageContext | None = None,
        state: StorageState | None = None,
    ) -> StorageContext:
        """Initialize storage components if not already initialized.

        This method initializes the NetworkX graph, DuckDB connection, and RDFLib store.
        If a custom implementation is set via set_delegate(), the call is delegated to that implementation.

        Args:
            db_path: Optional path to the DuckDB database file. If not provided,
                     the path is determined with the following precedence:
                     1. config.storage.duckdb.path
                     2. DUCKDB_PATH environment variable
                     3. Default to "kg.duckdb".
            context: Optional ``StorageContext`` to initialize. If not provided, the
                global context is used.

        Raises:
            StorageError: If the RDF store or VSS extension fails to initialize
                          and the failure is not due to a plugin registration issue.

        Returns:
            StorageContext: The initialized storage context.
        """
        st = state or StorageManager.state
        ctx = context or st.context
        if _delegate and _delegate is not StorageManager:
            return _delegate.setup(db_path, ctx)
        with st.lock:
            StorageManager.state = st
            StorageManager.context = ctx
            initialize_storage(db_path, context=ctx, state=st)
        return ctx

    @staticmethod
    def teardown(
        remove_db: bool = False,
        context: StorageContext | None = None,
        state: StorageState | None = None,
    ) -> None:
        """Close storage connections and optionally remove database files."""
        st = state or StorageManager.state
        ctx = context or st.context
        if _delegate and _delegate is not StorageManager:
            _delegate.teardown(remove_db, ctx, st)  # type: ignore[attr-defined]
            return
        StorageManager.state = st
        StorageManager.context = ctx
        teardown(remove_db, ctx, st)

    @staticmethod
    def _current_ram_mb() -> float:
        """Return RAM usage relative to the recorded baseline."""

        process_mb = _process_ram_mb()
        return max(0.0, process_mb - StorageManager.state.baseline_mb)

    @staticmethod
    def record_claim_audit(
        audit: ClaimAuditRecord | Mapping[str, Any]
    ) -> ClaimAuditRecord:
        """Persist a claim audit entry across storage backends."""

        if _delegate and _delegate is not StorageManager:
            return _delegate.record_claim_audit(audit)  # type: ignore[attr-defined]

        payload = audit.to_payload() if isinstance(audit, ClaimAuditRecord) else dict(audit)
        return StorageManager._persist_claim_audit_payload(payload)

    @staticmethod
    def list_claim_audits(claim_id: str | None = None) -> list[ClaimAuditRecord]:
        """Return persisted claim audits, optionally filtered by claim id."""

        if _delegate and _delegate is not StorageManager:
            return _delegate.list_claim_audits(claim_id)  # type: ignore[attr-defined]

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        payloads = StorageManager.context.db_backend.list_claim_audits(claim_id)
        return [ClaimAuditRecord.from_payload(p) for p in payloads]

    @staticmethod
    def _pop_lru() -> str | None:
        """Remove and return the least recently used node from the LRU cache.

        This method implements the "Least Recently Used" (LRU) eviction policy.
        See ``docs/algorithms/cache_eviction.md`` for analysis and proofs. It
        removes the node that was accessed least recently from the LRU cache
        and returns its ID. This is used by the _enforce_ram_budget method when
        the graph_eviction_policy is set to "lru".

        The LRU cache is an :class:`collections.OrderedDict` that maintains the
        order in which nodes were accessed, with the least recently used node at
        the beginning and the most recently used node at the end.  This method
        relies on that ordering and uses ``popitem(last=False)`` to remove the
        oldest entry.

        Returns:
            str | None: The ID of the least recently used node, or None if the cache is empty.

        Note:
            This method only removes the node from the LRU cache, not from the graph.
            The caller is responsible for removing the node from the graph if needed.
        """
        state = StorageManager.state
        with state.lock:
            lru = state.lru
            if not lru:
                return None
            node_id, _ = lru.popitem(last=False)
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
        with StorageManager.state.lock:
            graph = StorageManager.context.graph
            if not graph or not graph.nodes:
                return None
            node_id = cast(
                str,
                min(
                    graph.nodes,
                    key=lambda n: graph.nodes[n].get("confidence", 0.0),
                ),
            )
            lru = StorageManager.state.lru
            if node_id in lru:
                del lru[node_id]
        return node_id

    @staticmethod
    def _deterministic_node_limit(
        budget_mb: int, cfg: Any | None = None
    ) -> tuple[int | None, bool, int, int | None]:
        """Return the deterministic node limit and whether it is an override."""

        if cfg is None:
            cfg = ConfigLoader().config
        storage_cfg = getattr(cfg, "storage", None)
        override = None
        min_resident = _MIN_DETERMINISTIC_SURVIVORS
        if storage_cfg is not None:
            override = getattr(storage_cfg, "deterministic_node_budget", None)
            configured_min = getattr(
                storage_cfg,
                "minimum_deterministic_resident_nodes",
                _MIN_DETERMINISTIC_SURVIVORS,
            )
            try:
                min_resident = max(_MIN_DETERMINISTIC_SURVIVORS, int(configured_min))
            except (TypeError, ValueError):
                min_resident = _MIN_DETERMINISTIC_SURVIVORS

        if isinstance(override, int) and override >= 0:
            limit = override
            clamped_from = None
            if limit < min_resident:
                clamped_from = limit
                limit = min_resident
            return limit, True, min_resident, clamped_from
        if budget_mb > 0:
            derived_limit = max(0, budget_mb)
            final_limit = max(derived_limit, min_resident)
            clamped_from = derived_limit if final_limit != derived_limit else None
            return final_limit, False, min_resident, clamped_from
        return None, False, min_resident, None

    @staticmethod
    def _enforce_ram_budget(budget_mb: int) -> None:
        """Evict nodes from the graph when memory usage exceeds the configured budget.

        This method monitors the current RAM usage and evicts nodes from the graph
        when it exceeds the specified budget. The eviction policy is determined by
        the configuration:
        - "lru": Evicts the least recently used nodes first
        - "score": Evicts nodes with the lowest confidence scores first
        - "hybrid": Uses a combination of recency and confidence score
        - "adaptive": Dynamically selects the best policy based on usage patterns
        - "priority": Evicts nodes based on configurable priority tiers

        See ``docs/algorithms/cache_eviction.md`` for proofs of the LRU policy.
        The method continues evicting nodes until the RAM usage falls below the
        budget or there are no more nodes to evict. When operating system metrics
        stay flat even as usage exceeds the budget, or when a deterministic
        override is configured, the method falls back to a deterministic node
        budget so eviction remains predictable without violating the
        ``U ≤ B`` invariant.

        Args:
            budget_mb: The maximum amount of RAM to use in megabytes. If <= 0,
                      no eviction will occur.

        Note:
            Evicted nodes are removed from the in-memory graph but remain in the
            DuckDB and RDF stores. This allows for persistent storage while
            controlling memory usage.
            A 0 MB usage reading is treated as "unknown" and leaves the graph
            unchanged unless a deterministic override is active.

        Proof Sketch:
            Let ``U_0`` denote the initial RAM usage and ``T = B(1 - δ)`` the
            target bound, where ``B`` is the budget and ``δ`` the safety
            margin. Each iteration evicts a node consuming ``s_i > 0`` MB so the
            sequence ``U_{i+1} = U_i - s_i`` is strictly decreasing and bounded
            below by ``T``. Consequently there exists ``k`` such that
            ``U_k ≤ T`` and the loop halts after at most
            ``⌈(U_0 - T) / s_{ min}⌉`` iterations, yielding memory
            usage within the budget.
        """
        state = StorageManager.state
        with state.lock:
            if budget_mb <= 0:
                log.debug("RAM budget <= 0; skipping eviction")
                return

            current_mb = StorageManager._current_ram_mb()
            ram_measurement_available = current_mb > 0.0
            graph = StorageManager.context.graph
            if graph is None or not graph.nodes:
                return

            cfg = ConfigLoader().config
            policy = cfg.graph_eviction_policy.lower()
            lru = StorageManager.state.lru

            (
                deterministic_limit,
                deterministic_override,
                minimum_resident_nodes,
                clamped_from,
            ) = StorageManager._deterministic_node_limit(budget_mb, cfg)
            if clamped_from is not None and deterministic_limit is not None:
                source = "override" if deterministic_override else "derived"
                log.info(
                    "Deterministic node budget (%s=%d) below minimum %d; clamping to %d",
                    source,
                    clamped_from,
                    minimum_resident_nodes,
                    deterministic_limit,
                )
            if not ram_measurement_available and not deterministic_override:
                deterministic_limit = None
            over_budget = ram_measurement_available and current_mb > budget_mb
            needs_deterministic_budget = (
                deterministic_limit is not None and len(graph.nodes) > deterministic_limit
            )
            should_use_deterministic = needs_deterministic_budget and (
                deterministic_override or over_budget
            )

            if not over_budget and not deterministic_override and not should_use_deterministic:
                if not ram_measurement_available:
                    log.debug(
                        "RAM usage unavailable; skipping eviction without deterministic override"
                    )
                return

            use_deterministic_budget = False
            target_node_count: int | None = None
            mode = "ram"

            if should_use_deterministic:
                assert deterministic_limit is not None
                use_deterministic_budget = True
                target_node_count = deterministic_limit
                if not deterministic_override:
                    target_node_count = max(target_node_count, minimum_resident_nodes)
                    deterministic_limit = target_node_count
                mode = f"deterministic(limit={deterministic_limit})"
            elif deterministic_override:
                return

            eviction_start_time = time.time()
            nodes_evicted = 0
            starting_mb = current_mb
            starting_measurement_available = ram_measurement_available

            safety_margin = getattr(cfg, "eviction_safety_margin", 0.1)
            target_mb = budget_mb * (1 - safety_margin) if ram_measurement_available else None

            batch_size = min(
                getattr(cfg, "eviction_batch_size", 10),
                (max(1, len(graph.nodes) // 10) if graph and graph.nodes else 1),
            )

            if use_deterministic_budget:
                if target_node_count is None:
                    return
                removable = len(graph.nodes) - target_node_count
                if removable <= 0:
                    return
                batch_size = max(1, min(batch_size, removable))

            aggressive_threshold = budget_mb * 1.5
            aggressive_eviction = (
                not use_deterministic_budget
                and ram_measurement_available
                and current_mb > aggressive_threshold
            )

            current_display = f"{current_mb:.1f}MB" if ram_measurement_available else "unknown"
            target_display = f"{target_mb:.1f}MB" if target_mb is not None else "n/a"

            log.info(
                f"Starting eviction with policy={policy}, current={current_display}, "
                f"target={target_display}, mode={mode}, "
                f"aggressive={aggressive_eviction}, batch_size={batch_size}"
            )

            while StorageManager.context.graph:
                graph = StorageManager.context.graph
                if graph is None or not graph.nodes:
                    break

                if (
                    use_deterministic_budget
                    and not deterministic_override
                    and len(graph.nodes) <= minimum_resident_nodes
                ):
                    log.debug(
                        "Reached deterministic survivor floor (%d nodes); stopping eviction",
                        minimum_resident_nodes,
                    )
                    break

                ram_condition = (
                    ram_measurement_available and target_mb is not None and current_mb > target_mb
                )
                node_condition = (
                    use_deterministic_budget
                    and target_node_count is not None
                    and len(graph.nodes) > target_node_count
                )

                if not (ram_condition or node_condition):
                    break

                if use_deterministic_budget and node_condition:
                    assert target_node_count is not None
                    remaining = len(graph.nodes) - target_node_count
                    current_batch_size = min(batch_size, remaining)
                else:
                    current_batch_size = batch_size

                remaining_allowance: int | None = None
                if use_deterministic_budget:
                    assert target_node_count is not None
                    survivor_floor = max(target_node_count, minimum_resident_nodes)
                    remaining_allowance = max(0, len(graph.nodes) - survivor_floor)
                    if remaining_allowance <= 0:
                        log.debug(
                            "Deterministic mode reached survivor floor (%d nodes); stopping",
                            survivor_floor,
                        )
                        break
                    current_batch_size = min(current_batch_size, remaining_allowance)

                nodes_to_evict: list[str] = []

                if policy == "hybrid":
                    hybrid_scores: dict[str, float] = {}

                    recency_ranks: dict[str, float] = {}
                    for i, node_id in enumerate(reversed(lru)):
                        recency_ranks[node_id] = i / max(1, len(lru) - 1)

                    for node_id in graph.nodes:
                        if node_id in recency_ranks:
                            recency_weight = getattr(cfg, "recency_weight", 0.7)
                            confidence_weight = 1.0 - recency_weight

                            recency_score = recency_ranks.get(node_id, 1.0)
                            confidence_score = 1.0 - graph.nodes[node_id].get("confidence", 0.5)

                            hybrid_scores[node_id] = (
                                recency_weight * recency_score
                                + confidence_weight * confidence_score
                            )

                    candidates = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
                    nodes_to_evict = [node_id for node_id, _ in candidates[:current_batch_size]]

                elif policy == "adaptive":
                    if not hasattr(StorageManager, "_access_frequency"):
                        StorageManager._access_frequency = {}
                        StorageManager._last_adaptive_policy = "lru"

                    access_variance = 0.0
                    if StorageManager._access_frequency:
                        frequencies = list(StorageManager._access_frequency.values())
                        if frequencies:
                            mean = sum(frequencies) / len(frequencies)
                            variance = sum((f - mean) ** 2 for f in frequencies) / len(frequencies)
                            access_variance = variance

                    variance_threshold = getattr(cfg, "adaptive_variance_threshold", 5.0)
                    if access_variance > variance_threshold:
                        policy_to_use = "score"
                    else:
                        policy_to_use = "lru"

                    StorageManager._last_adaptive_policy = policy_to_use

                    if policy_to_use == "score":
                        for _ in range(current_batch_size):
                            popped = StorageManager._pop_low_score()
                            if popped and StorageManager.context.graph.has_node(popped):
                                nodes_to_evict.append(popped)
                    else:
                        for _ in range(current_batch_size):
                            popped = StorageManager._pop_lru()
                            if popped and StorageManager.context.graph.has_node(popped):
                                nodes_to_evict.append(popped)

                elif policy == "priority":
                    priority_tiers = {
                        "system": 0,
                        "user": 1,
                        "synthesis": 2,
                        "research": 3,
                        "default": 4,
                    }

                    if hasattr(cfg, "priority_tiers") and isinstance(cfg.priority_tiers, dict):
                        priority_tiers.update(cfg.priority_tiers)

                    node_priorities: dict[str, float] = {}
                    for node_id in graph.nodes:
                        node_type = graph.nodes[node_id].get("type", "default")
                        tier = priority_tiers.get(node_type, priority_tiers["default"])
                        confidence_boost = graph.nodes[node_id].get("confidence", 0.5) * 0.5
                        node_priorities[node_id] = tier - confidence_boost

                    candidates = sorted(node_priorities.items(), key=lambda x: x[1], reverse=True)
                    nodes_to_evict = [node_id for node_id, _ in candidates[:current_batch_size]]

                elif policy == "score":
                    for _ in range(current_batch_size):
                        popped = StorageManager._pop_low_score()
                        if popped and StorageManager.context.graph.has_node(popped):
                            nodes_to_evict.append(popped)

                elif policy == "lru":
                    while len(nodes_to_evict) < current_batch_size and StorageManager.state.lru:
                        popped = StorageManager._pop_lru()
                        if popped and StorageManager.context.graph.has_node(popped):
                            nodes_to_evict.append(popped)
                else:
                    while len(nodes_to_evict) < current_batch_size and StorageManager.state.lru:
                        popped = StorageManager._pop_lru()
                        if popped and StorageManager.context.graph.has_node(popped):
                            nodes_to_evict.append(popped)

                still_over_target = (
                    not use_deterministic_budget
                    and ram_measurement_available
                    and target_mb is not None
                    and current_mb > target_mb
                )
                fallback_needed = (
                    len(nodes_to_evict) < current_batch_size
                    and graph is not None
                    and graph.nodes
                    and (use_deterministic_budget or still_over_target)
                )
                if fallback_needed:
                    missing = current_batch_size - len(nodes_to_evict)
                    fallback_candidates: list[str] = []
                    for node_id in list(graph.nodes):
                        if node_id in nodes_to_evict:
                            continue
                        if not graph.has_node(node_id):
                            continue
                        fallback_candidates.append(node_id)
                        if len(fallback_candidates) >= missing:
                            break
                    if fallback_candidates:
                        log.debug(
                            "Eviction fallback selected %d graph nodes due to stale cache",
                            len(fallback_candidates),
                        )
                    nodes_to_evict.extend(fallback_candidates)

                if remaining_allowance is not None and len(nodes_to_evict) > remaining_allowance:
                    nodes_to_evict = nodes_to_evict[:remaining_allowance]

                if not nodes_to_evict:
                    break

                for node_id in nodes_to_evict:
                    if StorageManager.context.graph.has_node(node_id):
                        StorageManager.context.graph.remove_node(node_id)
                        if node_id in lru:
                            del lru[node_id]
                        StorageManager._access_frequency.pop(node_id, None)
                        EVICTION_COUNTER.inc()
                        nodes_evicted += 1

                current_mb = StorageManager._current_ram_mb()
                ram_measurement_available = current_mb > 0.0

                if not ram_measurement_available:
                    if use_deterministic_budget:
                        target_mb = None
                    else:
                        break

                if aggressive_eviction and not use_deterministic_budget and nodes_evicted > 50:
                    batch_size = min(
                        batch_size * 2,
                        (
                            len(StorageManager.context.graph.nodes) // 5
                            if StorageManager.context.graph and StorageManager.context.graph.nodes
                            else 1
                        ),
                    )

            eviction_time = time.time() - eviction_start_time
            final_mb = StorageManager._current_ram_mb()
            final_measurement_available = final_mb > 0.0
            mb_freed = starting_mb - final_mb
            freed_display = (
                f"{mb_freed:.1f}MB"
                if starting_measurement_available and final_measurement_available
                else "n/a"
            )
            final_display = f"{final_mb:.1f}MB" if final_measurement_available else "unknown"

            log.info(
                f"Eviction completed: policy={policy}, nodes_evicted={nodes_evicted}, "
                f"time={eviction_time:.2f}s, memory_freed={freed_display}, "
                f"final={final_display}, mode={mode}"
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
                suggestion="Ensure the claim is a dictionary with required fields",
            )

        # Check for required fields
        required_fields = ["id", "type", "content"]
        for key in required_fields:
            if key not in claim:
                raise StorageError(
                    f"Missing required field: '{key}'",
                    suggestion=f"Ensure the claim has a '{key}' field",
                )

            # Check that the field is a string
            if not isinstance(claim[key], str):
                raise StorageError(
                    f"Invalid '{key}' field: expected string",
                    suggestion=f"Ensure the '{key}' field is a string",
                )

    @staticmethod
    def _ensure_storage_initialized() -> None:
        """Ensure all storage components are initialized before performing operations.

        This method checks if the DuckDB backend, NetworkX graph, and RDF store
        are initialized. If any of them are not initialized, it attempts to initialize
        them by calling setup(). If initialization fails or any component remains
        uninitialized after setup, a StorageError is raised with a specific message
        indicating which component failed to initialize.

        Raises:
            StorageError: If any storage component cannot be initialized or remains
                         uninitialized after calling setup(). The error message includes
                         a suggestion to call StorageManager.setup() before performing operations.
        """
        if StorageManager.context.db_backend is None or StorageManager.context.graph is None:
            try:
                initialize_storage(context=StorageManager.context, state=StorageManager.state)
            except Exception as e:
                raise StorageError("Failed to initialize storage components", cause=e)

        if StorageManager.context.db_backend is None:
            raise StorageError(
                "DuckDB backend not initialized",
                suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations",
            )
        if StorageManager.context.graph is None:
            raise StorageError(
                "Graph not initialized",
                suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations",
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
        state = StorageManager.state
        with state.lock:
            attrs = dict(claim.get("attributes", {}))
            if "confidence" in claim:
                attrs["confidence"] = claim["confidence"]
            if "audit" in claim:
                attrs["audit"] = claim["audit"]
            assert StorageManager.context.graph is not None
            StorageManager.context.graph.add_node(claim["id"], **attrs)
            # Increment the counter and store it to maintain deterministic
            # ordering.  A re-entrant lock ensures concurrent writers cannot
            # race on the counter or LRU structure.
            state.lru_counter += 1
            state.lru[claim["id"]] = state.lru_counter
            for rel in claim.get("relations", []):
                assert StorageManager.context.graph is not None
                StorageManager.context.graph.add_edge(
                    rel["src"],
                    rel["dst"],
                    **rel.get("attributes", {}),
                )

    @staticmethod
    def _persist_claim_audit_payload(audit_payload: Mapping[str, Any]) -> ClaimAuditRecord:
        """Persist verification metadata across storage backends."""

        record = ClaimAuditRecord.from_payload(dict(audit_payload))
        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        StorageManager.context.db_backend.persist_claim_audit(record.to_payload())

        graph = StorageManager.context.graph
        if graph is not None and graph.has_node(record.claim_id):
            graph.nodes[record.claim_id]["audit"] = record.to_payload()
        return record

    @staticmethod
    def _persist_to_duckdb(claim: dict[str, Any]) -> None:
        """Persist a claim to the DuckDB relational database.

        This method inserts the claim into three tables in DuckDB:
        1. nodes: Stores the claim's ID, type, content, and confidence score
        2. edges: Stores relationships between claims (if any)
        3. embeddings: Stores the claim's vector embedding (if available)

        The DuckDB database provides persistent storage and supports vector search
        through the VSS extension. Unlike the NetworkX graph, data in DuckDB
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
        # Use the DuckDBStorageBackend to persist the claim
        assert StorageManager.context.db_backend is not None
        StorageManager.context.db_backend.persist_claim(claim)

    @staticmethod
    def _persist_to_kuzu(claim: dict[str, Any]) -> None:
        """Persist a claim to the Kuzu graph database."""
        if _kuzu_backend is None:
            return
        _kuzu_backend.persist_claim(claim)

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
        if StorageManager.context.rdf_store is None:
            # RDF backend not available; skip semantic persistence.
            return
        subj = rdflib.URIRef(f"urn:claim:{claim['id']}")
        for k, v in claim.get("attributes", {}).items():
            pred = rdflib.URIRef(f"urn:prop:{k}")
            obj = rdflib.Literal(v)
            StorageManager.context.rdf_store.add((subj, pred, obj))

        # Apply ontology reasoning so advanced queries see inferred triples
        run_ontology_reasoner(StorageManager.context.rdf_store)

    @staticmethod
    def persist_claim(claim: dict[str, Any], partial_update: bool = False) -> None:
        """Persist a claim to all storage backends with support for incremental updates.

        This method validates the claim, ensures storage is initialized, and then
        persists the claim to all three backends (NetworkX, DuckDB, and RDF).
        It supports incremental updates to existing claims, allowing for efficient
        updates without replacing the entire claim.

        After persistence, it checks RAM usage and evicts older claims if needed
        based on the configured RAM budget.

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Args:
            claim: The claim to persist as a dictionary. Must contain 'id', 'content',
                  and may contain 'embedding', 'sources', and other attributes.
            partial_update: If True, treat this as a partial update to an existing claim,
                          merging with existing data rather than replacing it completely.
                          Default is False.

        Raises:
            StorageError: If the claim is invalid (missing required fields or
                         incorrect types) or if storage is not initialized properly.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.persist_claim(claim, partial_update)

        if _message_queue is not None:
            _message_queue.put(
                {
                    "action": "persist_claim",
                    "claim": claim,
                    "partial_update": partial_update,
                }
            )
            return

        # Validate claim
        StorageManager._validate_claim(claim)

        with StorageManager.state.lock:
            # Ensure storage is initialized
            StorageManager._ensure_storage_initialized()

            # Check if this is an update to an existing claim
            claim_id = claim["id"]
            existing_claim = None
            is_update = False

            # Track timing for performance metrics
            import time

            start_time = time.time()

            # Check if the claim already exists in the graph
            assert StorageManager.context.graph is not None
            if StorageManager.context.graph.has_node(claim_id):
                is_update = True
                if partial_update:
                    # Get the existing claim data
                    existing_claim = StorageManager.context.graph.nodes[claim_id].copy()

                    # Merge the new claim data with the existing data
                    # Note: We're careful not to modify the input claim
                    merged_claim = existing_claim.copy()

                    # Ensure the claim id is preserved for downstream persistence
                    merged_claim["id"] = claim_id

                    # Update basic fields if provided
                    if "type" in claim:
                        merged_claim["type"] = claim["type"]
                    if "content" in claim:
                        merged_claim["content"] = claim["content"]

                    # Update nested fields
                    for key, value in claim.items():
                        if key not in ["id", "type", "content"]:
                            if (
                                isinstance(value, dict)
                                and key in merged_claim
                                and isinstance(merged_claim[key], dict)
                            ):
                                # Deep merge dictionaries
                                merged_claim[key].update(value)
                            else:
                                # Replace or add other fields
                                merged_claim[key] = value

                    # Use the merged claim for persistence
                    claim_to_persist = merged_claim

                    log.debug(
                        f"Performing partial update of claim {claim_id} "
                        f"(merged {len(claim)} fields with existing data)"
                    )
                else:
                    # Full replacement of existing claim
                    claim_to_persist = claim
                    log.debug(f"Replacing existing claim {claim_id}")
            else:
                # New claim
                claim_to_persist = claim
                log.debug(f"Persisting new claim {claim_id}")

            # Add timestamp for tracking
            if "metadata" not in claim_to_persist:
                claim_to_persist["metadata"] = {}

            # Add or update timestamps
            current_time = time.time()
            if is_update:
                claim_to_persist["metadata"]["updated_at"] = current_time
            else:
                claim_to_persist["metadata"]["created_at"] = current_time
                claim_to_persist["metadata"]["updated_at"] = current_time

            # Persist to all backends with appropriate update mode
            StorageManager._persist_to_networkx(claim_to_persist)

            audit_payload = claim_to_persist.get("audit")
            if isinstance(audit_payload, Mapping):
                payload = dict(audit_payload)
                payload.setdefault("claim_id", claim_id)
                StorageManager._persist_claim_audit_payload(payload)

            # For database backends, use different methods for updates vs. new claims
            assert StorageManager.context.db_backend is not None
            if is_update:
                # Update existing records
                StorageManager.context.db_backend.update_claim(claim_to_persist, partial_update)
                StorageManager._update_rdf_claim(claim_to_persist, partial_update)
                StorageManager._persist_to_kuzu(claim_to_persist)
            else:
                # Insert new records
                StorageManager.context.db_backend.persist_claim(claim_to_persist)
                StorageManager._persist_to_rdf(claim_to_persist)
                StorageManager._persist_to_kuzu(claim_to_persist)

            # Refresh vector index if embeddings were provided
            if claim.get("embedding") is not None and StorageManager.has_vss():
                try:
                    StorageManager.refresh_vector_index()
                except Exception as e:
                    log.warning(f"Failed to refresh vector index: {e}")

            # Update LRU cache to mark this claim as recently used
            StorageManager.touch_node(claim_id)

            # Log performance metrics
            persistence_time = time.time() - start_time
            log.debug(
                f"Claim persistence completed in {persistence_time:.4f}s "
                f"(id={claim_id}, update={is_update}, partial={partial_update})"
            )

            # Check RAM usage and evict if needed
            budget = ConfigLoader().config.ram_budget_mb
            StorageManager._enforce_ram_budget(budget)

    @staticmethod
    def update_claim(claim: dict[str, Any], partial_update: bool = False) -> None:
        """Update an existing claim across storage backends.

        This method delegates to the configured database backend. When a message
        queue is configured, the update request is placed on the queue for
        asynchronous processing.

        Args:
            claim: Claim data containing at least an ``id`` field.
            partial_update: If ``True``, only the provided fields are updated.

        Raises:
            StorageError: If storage is not initialized or the backend update
                fails.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.update_claim(claim, partial_update)

        if _message_queue is not None:
            _message_queue.put(
                {
                    "action": "update_claim",
                    "claim": claim,
                    "partial_update": partial_update,
                }
            )
            return

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        StorageManager.context.db_backend.update_claim(claim, partial_update)

        audit_payload = claim.get("audit")
        if isinstance(audit_payload, Mapping):
            payload = dict(audit_payload)
            payload.setdefault("claim_id", claim.get("id", ""))
            if payload.get("claim_id"):
                StorageManager._persist_claim_audit_payload(payload)

    @staticmethod
    def get_claim(claim_id: str) -> dict[str, Any]:
        """Retrieve a persisted claim from DuckDB."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.get_claim(claim_id)

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        return StorageManager.context.db_backend.get_claim(claim_id)

    @staticmethod
    def _update_rdf_claim(claim: dict[str, Any], partial_update: bool = False) -> None:
        """Update an existing claim in the RDF store.

        This method updates an existing claim in the RDF store, either by completely
        replacing it or by merging new data with existing data.

        Args:
            claim: The claim to update
            partial_update: If True, merge with existing data rather than replacing
        """
        assert StorageManager.context.rdf_store is not None
        subj = rdflib.URIRef(f"urn:claim:{claim['id']}")

        if not partial_update:
            # Remove all existing triples for this subject
            for s, p, o in StorageManager.context.rdf_store.triples((subj, None, None)):
                StorageManager.context.rdf_store.remove((s, p, o))

        # Add new triples
        for k, v in claim.get("attributes", {}).items():
            pred = rdflib.URIRef(f"urn:prop:{k}")
            obj = rdflib.Literal(v)
            StorageManager.context.rdf_store.add((subj, pred, obj))
        # Apply ontology reasoning so updates expose inferred triples
        run_ontology_reasoner(StorageManager.context.rdf_store)

    @staticmethod
    def update_rdf_claim(claim: dict[str, Any], partial_update: bool = False) -> None:
        """Public wrapper around :func:`_update_rdf_claim`."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.update_rdf_claim(claim, partial_update)

        StorageManager._ensure_storage_initialized()
        StorageManager._update_rdf_claim(claim, partial_update)

    @staticmethod
    def create_hnsw_index() -> None:
        """Create a Hierarchical Navigable Small World (HNSW) index on the embeddings table.

        This method creates an HNSW index on the embeddings table to enable efficient
        approximate nearest neighbor search. The index parameters (m, ef_construction, metric)
        are configured via the storage configuration.

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Raises:
            StorageError: If the index creation fails.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.create_hnsw_index()

        # Ensure storage is initialized
        if StorageManager.context.db_backend is None:
            setup(context=StorageManager.context, state=StorageManager.state)
        assert StorageManager.context.db_backend is not None

        # Use the DuckDBStorageBackend to create the HNSW index
        try:
            StorageManager.context.db_backend.create_hnsw_index()
        except Exception as e:
            raise StorageError("Failed to create HNSW index", cause=e)

    @staticmethod
    def refresh_vector_index() -> None:
        """Rebuild the vector index to include new embeddings."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.refresh_vector_index()

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        try:
            StorageManager.context.db_backend.refresh_hnsw_index()
        except Exception as e:
            raise StorageError("Failed to refresh HNSW index", cause=e)

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
                suggestion="Ensure the query_embedding is a list of float values",
            )

        if not all(isinstance(x, (int, float)) for x in query_embedding):
            raise StorageError(
                "Invalid query_embedding values: expected numeric values",
                suggestion="Ensure all values in query_embedding are numbers",
            )

        if len(query_embedding) == 0:
            raise StorageError(
                "Empty query_embedding",
                suggestion="Provide a non-empty list of float values for query_embedding",
            )

        if not isinstance(k, int) or k <= 0:
            raise StorageError(
                "Invalid k value: expected positive integer",
                suggestion="Ensure k is a positive integer",
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
    def vector_search(query_embedding: list[float], k: int = 5) -> list[dict[str, Any]]:
        """Search for claims by vector similarity.

        This method performs a vector similarity search using the provided query
        embedding. It validates the search parameters, ensures storage is
        initialized, and then executes the search using the DuckDB VSS extension
        if available. The search uses cosine similarity by default (configurable
        via ``storage.hnsw_metric``) and returns the ``k`` most similar claims,
        ordered by similarity score.

        If the VSS extension is not loaded, an empty list is returned. If a
        custom implementation is set via ``set_delegate()``, the call is
        delegated to that implementation.

        Args:
            query_embedding: The query embedding vector as a list of floats.
                            Must be non-empty and contain only numeric values.
            k: The number of results to return. Must be a positive integer.
                Default is 5.

        Returns:
            list[dict[str, Any]]: List of nearest nodes with their embeddings and
                                 similarity scores, ordered by similarity (highest first).
                                 Each result contains 'node_id' and 'embedding'.

        Raises:
            StorageError: If the search parameters are invalid or storage is not
                initialized.
            NotFoundError: If no embeddings are found in the database.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.vector_search(query_embedding, k)

        # Validate parameters
        StorageManager._validate_vector_search_params(query_embedding, k)

        # Ensure storage is initialized
        StorageManager._ensure_storage_initialized()

        # Check if VSS extension is available
        if not StorageManager.has_vss():
            return []

        # Use the DuckDBStorageBackend to perform the vector search
        db_backend = StorageManager.context.db_backend
        if db_backend is None:  # Safety check for type checkers
            raise StorageError(
                "DuckDB backend not initialized",
                suggestion="Call StorageManager.setup() before vector_search",
            )
        try:
            return db_backend.vector_search(query_embedding, k)
        except Exception as e:
            raise StorageError(
                "Vector search failed",
                cause=e,
                suggestion="Check that the VSS extension is properly installed and that embeddings exist in the database",
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
        with StorageManager.state.lock:
            if StorageManager.context.graph is None:
                try:
                    setup(context=StorageManager.context, state=StorageManager.state)
                except Exception as e:
                    raise NotFoundError("Graph not initialized", cause=e)
            if StorageManager.context.graph is None:
                raise NotFoundError("Graph not initialized")
            return StorageManager.context.graph

    @staticmethod
    def touch_node(node_id: str) -> None:
        """Update access time for a node in the LRU cache.

        This method updates the access timestamp for a node in the LRU (Least
        Recently Used) cache and moves it to the end of the cache order,
        marking it as most recently used.  It also increments an access
        counter used by hybrid and adaptive eviction policies.  The
        implementation relies on the ordering properties of
        :class:`collections.OrderedDict`, meaning older entries remain at the
        beginning and are evicted first when the RAM budget is exceeded.

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Args:
            node_id: The ID of the node to update.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.touch_node(node_id)
        state = StorageManager.state
        lru = state.lru
        with state.lock:
            state.lru_counter += 1
            lru[node_id] = state.lru_counter
            # ``move_to_end`` maintains the deque order for faster popping
            lru.move_to_end(node_id)
            StorageManager._access_frequency[node_id] = (
                StorageManager._access_frequency.get(node_id, 0) + 1
            )

    @staticmethod
    def get_duckdb_conn() -> DuckDBConnection:
        """Get the DuckDB connection used for relational storage.

        This method returns the global DuckDB connection used for relational
        storage of claims and their embeddings. If the connection is not initialized,
        it attempts to initialize it by calling setup().

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Returns:
            DuckDBConnection: The DuckDB connection instance.

        Raises:
            NotFoundError: If the connection cannot be initialized or remains None after initialization.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.get_duckdb_conn()
        with StorageManager.state.lock:
            if StorageManager.context.db_backend is None:
                try:
                    setup(context=StorageManager.context, state=StorageManager.state)
                except Exception as e:
                    raise NotFoundError("DuckDB connection not initialized", cause=e)
            if StorageManager.context.db_backend is None:
                raise NotFoundError("DuckDB connection not initialized")
            return StorageManager.context.db_backend.get_connection()

    @staticmethod
    @contextmanager
    def connection() -> Iterator[DuckDBConnection]:
        """Borrow a DuckDB connection from the pool."""
        if _delegate and _delegate is not StorageManager:
            with _delegate.connection() as conn:
                yield conn
            return
        with StorageManager.state.lock:
            if StorageManager.context.db_backend is None:
                setup(context=StorageManager.context, state=StorageManager.state)
            backend = StorageManager.context.db_backend
        if backend is None:
            raise NotFoundError("DuckDB connection not initialized")
        with backend.connection() as conn:
            yield conn

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
        with StorageManager.state.lock:
            if StorageManager.context.rdf_store is None:
                try:
                    setup(context=StorageManager.context, state=StorageManager.state)
                except Exception as e:
                    raise NotFoundError("RDF store not initialized", cause=e)
            if StorageManager.context.rdf_store is None:
                raise NotFoundError("RDF store not initialized")
            return StorageManager.context.rdf_store

    @staticmethod
    def get_rdf_backend_identifier() -> str:
        """Return the identifier of the configured RDF store.

        Returns:
            str: Name of the underlying RDF backend. Defaults to the store's
            class name when no explicit identifier is present.

        Raises:
            NotFoundError: If the RDF store is not initialized.
        """
        store = StorageManager.get_rdf_store()
        return getattr(store.store, "identifier", store.store.__class__.__name__)

    @staticmethod
    def has_vss() -> bool:
        """Check if the VSS extension is available for vector search.

        This method checks if the VSS extension is loaded and available for
        vector search operations. If the storage system is not initialized,
        it attempts to initialize it by calling setup().

        If a custom implementation is set via set_delegate(), the call is
        delegated to that implementation.

        Returns:
            bool: True if the VSS extension is loaded and available, False otherwise.
        """
        if _delegate and _delegate is not StorageManager:
            return _delegate.has_vss()
        with StorageManager.state.lock:
            if StorageManager.context.db_backend is None:
                try:
                    setup(context=StorageManager.context, state=StorageManager.state)
                except Exception:
                    return False
            if StorageManager.context.db_backend is None:
                return False
            return StorageManager.context.db_backend.has_vss()

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
        with StorageManager.state.lock:
            if StorageManager.context.graph is not None:
                StorageManager.context.graph.clear()
            if StorageManager.context.db_backend is not None:
                StorageManager.context.db_backend.clear()
            if StorageManager.context.rdf_store is not None:
                StorageManager.context.rdf_store.remove((None, None, None))
            # Clear LRU cache to keep state consistent
            state = StorageManager.state
            state.lru.clear()
            state.lru_counter = 0
            if hasattr(StorageManager, "_access_frequency"):
                StorageManager._access_frequency.clear()
            state.baseline_mb = _process_ram_mb()

    # ------------------------------------------------------------------
    # Ontology-based reasoning utilities
    # ------------------------------------------------------------------

    @staticmethod
    def load_ontology(path: str) -> None:
        """Load an ontology file into the RDF store.

        The ontology is parsed and all triples are added to the current
        RDF store. Supported formats are those understood by ``rdflib``
        (e.g. ``ttl``, ``xml``).
        """
        StorageManager._ensure_storage_initialized()
        store = StorageManager.get_rdf_store()
        store.parse(path)

    @staticmethod
    def apply_ontology_reasoning(engine: Optional[str] = None) -> None:
        """Apply ontology reasoning over the RDF store using the chosen engine."""
        StorageManager._ensure_storage_initialized()
        cfg = _get_config()
        store = StorageManager.get_rdf_store()
        configured_backend = getattr(cfg, "rdf_backend", "memory").lower()
        actual_backend = getattr(
            store.store,
            "identifier",
            store.store.__class__.__name__,
        ).lower()
        if configured_backend == "memory" and actual_backend not in {"memory", "iomemory"}:
            preserved_triples = list(store.triples((None, None, None)))
            preserved_namespaces = list(store.namespaces())
            with StorageManager.state.lock:
                _reset_context(StorageManager.context)
                setup(context=StorageManager.context, state=StorageManager.state)
                store = StorageManager.context.rdf_store or StorageManager.get_rdf_store()
                for prefix, namespace in preserved_namespaces:
                    try:
                        store.bind(prefix, namespace, override=True)
                    except Exception:  # pragma: no cover - namespace restoration best-effort
                        log.debug("Failed to restore namespace binding", exc_info=True)
                for triple in preserved_triples:
                    store.add(triple)
        run_ontology_reasoner(store, engine)

    @staticmethod
    def infer_relations() -> None:
        """Infer new triples using the configured ontology reasoner."""
        StorageManager._ensure_storage_initialized()
        reasoner = getattr(ConfigLoader().config.storage, "ontology_reasoner", "owlrl")
        if ":" in reasoner and reasoner != "owlrl":  # custom engine
            try:  # pragma: no cover - optional dependency
                module, func = reasoner.split(":", maxsplit=1)
                engine_mod = __import__(module, fromlist=[func])
                getattr(engine_mod, func)(StorageManager.get_rdf_store())
            except Exception as exc:  # pragma: no cover - optional dependency
                raise StorageError(
                    "Failed to run external ontology reasoner",
                    cause=exc,
                    suggestion="Check storage.ontology_reasoner configuration",
                )
        else:
            StorageManager.apply_ontology_reasoning(reasoner)

    @staticmethod
    def query_rdf(query: str) -> rdflib.query.Result:
        """Run a SPARQL query against the RDF store."""
        StorageManager._ensure_storage_initialized()
        store = StorageManager.get_rdf_store()
        return store.query(query)

    @staticmethod
    def query_ontology(query: str) -> rdflib.query.Result:
        """Run a SPARQL query against the ontology graph."""
        return StorageManager.query_rdf(query)

    @staticmethod
    def query_with_reasoning(query: str, engine: Optional[str] = None) -> rdflib.query.Result:
        """Run a SPARQL query after applying ontology reasoning."""
        StorageManager._ensure_storage_initialized()
        store = StorageManager.get_rdf_store()
        run_ontology_reasoner(store, engine)
        return store.query(query)

    @staticmethod
    def visualize_rdf(output_path: str) -> None:
        """Generate a simple PNG visualization of the RDF graph."""
        StorageManager._ensure_storage_initialized()
        store = StorageManager.get_rdf_store()
        from .visualization import save_rdf_graph

        save_rdf_graph(store, output_path)


class EvictionPolicy:
    """Base class for simple eviction policy simulations."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity

    def record(self, key: str) -> str | None:
        """Record access to ``key`` and return any evicted item."""
        raise NotImplementedError


class FIFOEvictionPolicy(EvictionPolicy):
    """First-in, first-out eviction policy."""

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self._queue: deque[str] = deque()

    def record(self, key: str) -> str | None:
        if key in self._queue:
            return None
        self._queue.append(key)
        if len(self._queue) > self.capacity:
            return self._queue.popleft()
        return None


class LRUEvictionPolicy(EvictionPolicy):
    """Least recently used eviction policy."""

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self._order: OrderedDict[str, None] = OrderedDict()

    def record(self, key: str) -> str | None:
        if key in self._order:
            self._order.move_to_end(key)
        else:
            self._order[key] = None
        if len(self._order) > self.capacity:
            evicted, _ = self._order.popitem(last=False)
            return evicted
        return None
