"""
Hybrid Distributed Knowledge Graph (DKG) persistence system.

This module provides a storage system that combines three backends:
1. NetworkX: For in-memory graph storage and traversal
2. DuckDB: For relational storage and vector search
3. RDFLib: For semantic graph storage and SPARQL queries

The storage system supports claim persistence, vector search, and automatic
resource management with configurable eviction policies. See
``docs/algorithms/cache_eviction.md`` for proofs of the LRU policy.

Custom storage implementations can be injected using
``StorageDelegateProtocol`` which captures the static interface expected by the
default manager. This keeps monkeypatched delegates type-safe while satisfying
the repository's strict typing guidelines.

Note on VSS Extension:
The vector search functionality requires the DuckDB VSS extension.
If the extension is not available, the system continues to operate but
vector search calls return empty results. Claims and embeddings are still
stored in the database.
The system attempts to install and load the VSS extension automatically
if it's enabled in the configuration.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import time
from collections import OrderedDict, defaultdict, deque
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from threading import RLock
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    cast,
    Protocol,
)
from uuid import uuid4

import networkx as nx
from networkx.readwrite import json_graph
import rdflib
from .config import ConfigLoader, StorageConfig
from .config.models import NamespaceMergeConfig, NamespaceMergeStrategy
from .errors import ConfigError, NotFoundError, StorageError
from .kg_reasoning import run_ontology_reasoner
from .logging_utils import get_logger
from .orchestration.metrics import EVICTION_COUNTER
from .storage_utils import (
    DEFAULT_NAMESPACE_LABEL,
    NamespaceTokens,
    canonical_namespace,
    graph_add,
    graph_triples,
    namespace_table_suffix,
    normalise_workspace_slug,
    resolve_namespace,
    serialise_workspace_resource,
)
from .storage_backends import DuckDBStorageBackend, init_rdf_store
from .storage_typing import (
    DuckDBConnectionProtocol,
    GraphProtocol,
    JSONDict,
    JSONDictList,
    JSONMapping,
    RDFTriple,
    RDFTriplePattern,
    ensure_mutable_mapping,
    to_json_dict,
)

if TYPE_CHECKING:  # pragma: no cover
    from .storage_backends import KuzuStorageBackend
    from .distributed.broker import PersistClaimMessage, StorageQueueProtocol
else:  # pragma: no cover - runtime typing compatibility
    from .distributed.broker import StorageQueueProtocol

# Typed reference to the optional Kuzu backend.
KuzuBackend: type[KuzuStorageBackend] | None = None

# Determine availability of the optional Kuzu dependency without importing it
try:  # pragma: no cover - optional dependency
    _has_kuzu = importlib.util.find_spec("kuzu") is not None
except Exception:  # pragma: no cover - defensive
    _has_kuzu = False

if _has_kuzu:  # pragma: no cover - optional dependency
    from .storage_backends import KuzuStorageBackend as _KuzuStorageBackend

    KuzuBackend = _KuzuStorageBackend

# Alias the DuckDB protocol for readability within this module.
DuckDBConnection = DuckDBConnectionProtocol


@dataclass
class StorageContext:
    """Container for storage backend instances."""

    graph: Optional[nx.DiGraph[Any]] = None
    kg_graph: Optional[nx.MultiDiGraph[Any]] = None
    db_backend: Optional[DuckDBStorageBackend] = None
    rdf_store: Optional[GraphProtocol] = None
    config_fingerprint: Optional[str] = None
    rdf_namespaces: dict[str, GraphProtocol] = field(default_factory=dict)


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

# Reusable typing helpers -------------------------------------------------


def _persist_claim_message(
    claim: JSONDict, partial_update: bool, namespace: str | None
) -> "PersistClaimMessage":
    """Return a broker-compatible payload for claim persistence."""

    payload: "PersistClaimMessage" = {
        "action": "persist_claim",
        "claim": claim,
        "partial_update": partial_update,
    }
    if namespace is not None:
        payload["namespace"] = namespace
    return payload


def _as_rdf_triple(subject: Any, predicate: Any, obj: Any) -> RDFTriple:
    """Return a typed RDF triple for mypy compatibility."""

    return cast(RDFTriple, (subject, predicate, obj))


# Optional injection point for tests


class StorageDelegateProtocol(Protocol):
    """Typed interface for swapping :class:`StorageManager` implementations."""

    @staticmethod
    def setup(db_path: Optional[str], context: StorageContext) -> StorageContext: ...

    @staticmethod
    def teardown(remove_db: bool, context: StorageContext, state: "StorageState") -> None: ...

    @staticmethod
    def record_claim_audit(
        audit: ClaimAuditRecord | JSONMapping,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> ClaimAuditRecord: ...

    @staticmethod
    def list_claim_audits(
        claim_id: str | None = None,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> list[ClaimAuditRecord]: ...

    @staticmethod
    def save_workspace_manifest(
        manifest: WorkspaceManifest | JSONMapping,
        *,
        increment_version: bool = True,
    ) -> WorkspaceManifest: ...

    @staticmethod
    def save_scholarly_paper(record: JSONMapping) -> JSONDict: ...

    @staticmethod
    def list_scholarly_papers(
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
        provider: str | None = None,
    ) -> list[JSONDict]: ...

    @staticmethod
    def get_scholarly_paper(
        namespace: NamespaceTokens | Mapping[str, str] | str,
        provider: str,
        paper_id: str,
    ) -> JSONDict: ...

    @staticmethod
    def get_workspace_manifest(
        workspace_id: str,
        version: int | None = None,
        manifest_id: str | None = None,
    ) -> WorkspaceManifest: ...

    @staticmethod
    def list_workspace_manifests(
        workspace_id: str | None = None,
    ) -> list[WorkspaceManifest]: ...

    @staticmethod
    def merge_claim_groups(
        claims_by_namespace: Mapping[str, Sequence[JSONMapping]],
        policy: str | NamespaceMergeConfig | None = None,
    ) -> list[JSONDict]: ...


_delegate: StorageDelegateProtocol | None = None
# Optional queue for distributed persistence
_message_queue: "StorageQueueProtocol | None" = None

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


def ensure_source_id(source: JSONMapping) -> JSONDict:
    """Return a copy of ``source`` with a stable ``source_id`` fingerprint."""

    enriched = to_json_dict(source)
    existing = enriched.get("source_id") or enriched.get("id")
    if existing:
        enriched["source_id"] = str(existing)
        return enriched

    snippet = enriched.get("snippet") or enriched.get("content") or ""
    snippet_text = snippet if isinstance(snippet, str) else repr(snippet)
    fingerprint = "|".join(
        [
            str(enriched.get("url", "")),
            str(enriched.get("title", "")),
            snippet_text[:200],
        ]
    )
    digest = hashlib.sha256(fingerprint.encode("utf-8", "ignore")).hexdigest()[:12]
    enriched["source_id"] = f"src-{digest}"
    return enriched


@dataclass(slots=True)
class ClaimAuditRecord:
    """Structured verification metadata stored alongside claims.

    The record captures FEVER-style verification attributes together with a
    ``provenance`` mapping that encodes how the audit was produced. The
    mapping is expected to contain at least three namespaces:

    - ``retrieval`` – query text, generated variants, and lookup events.
    - ``backoff`` – retry counters, sampled paraphrases, and rate limiting.
    - ``evidence`` – stable identifiers for the snippets or prior audits that
      informed the verdict.

    Downstream consumers can rely on this structure to trace how each claim
    audit was assembled and to reproduce the retrieval process if needed.
    """

    claim_id: str
    status: ClaimAuditStatus
    entailment_score: float | None = None
    sources: list[JSONDict] = field(default_factory=list)
    notes: str | None = None
    entailment_variance: float | None = None
    instability_flag: bool | None = None
    sample_size: int | None = None
    provenance: JSONDict = field(default_factory=dict)
    audit_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: float = field(default_factory=time.time)
    namespace: str | None = None

    def to_payload(self) -> JSONDict:
        """Serialise the record into a JSON-compatible payload.

        Returns:
            JSONDict: A mapping suitable for persistence layers. The
            ``provenance`` field is copied to avoid mutating the dataclass
            state when callers adjust nested metadata.
        """

        return {
            "audit_id": self.audit_id,
            "claim_id": self.claim_id,
            "status": self.status.value,
            "entailment_score": self.entailment_score,
            "entailment_variance": self.entailment_variance,
            "instability_flag": self.instability_flag,
            "sample_size": self.sample_size,
            "sources": self.sources,
            "provenance": ensure_mutable_mapping(self.provenance),
            "notes": self.notes,
            "created_at": self.created_at,
            "namespace": self.namespace,
        }

    @classmethod
    def from_payload(cls, payload: JSONMapping) -> "ClaimAuditRecord":
        """Create a record from a dictionary payload.

        Args:
            payload: Mapping produced by :meth:`to_payload` or a serialised
                representation retrieved from storage.

        Returns:
            ClaimAuditRecord: The reconstructed audit.
        """

        status_value = payload.get("status", ClaimAuditStatus.NEEDS_REVIEW)
        if isinstance(status_value, ClaimAuditStatus):
            status = status_value
        else:
            try:
                status = ClaimAuditStatus(str(status_value))
            except ValueError as exc:  # pragma: no cover - defensive
                raise StorageError("Invalid claim audit status") from exc
        sources_raw = payload.get("sources") or []
        if not isinstance(sources_raw, Sequence) or isinstance(sources_raw, (str, bytes)):
            raise StorageError("sources must be a sequence of mappings")
        serialised_sources: list[JSONDict] = []
        for src in sources_raw:
            if isinstance(src, Mapping):
                serialised_sources.append(to_json_dict(src))
            else:
                raise StorageError("each source must be a mapping")
        provenance_raw = payload.get("provenance") or {}
        if isinstance(provenance_raw, Mapping):
            provenance = to_json_dict(provenance_raw)
        elif isinstance(provenance_raw, str):
            try:
                parsed = json.loads(provenance_raw)
            except json.JSONDecodeError:
                parsed = {}
            provenance = to_json_dict(parsed) if isinstance(parsed, Mapping) else {}
        else:
            raise StorageError("provenance must be a mapping")
        created_at_value = payload.get("created_at")
        if created_at_value is None:
            created_at = time.time()
        else:
            created_at = float(cast(float | int | str, created_at_value))
        audit_id_value = payload.get("audit_id")
        audit_id = str(audit_id_value) if audit_id_value is not None else str(uuid4())
        claim_id_value = payload.get("claim_id")
        claim_id = str(claim_id_value) if claim_id_value is not None else ""
        if not claim_id:
            raise StorageError("claim_id is required for claim audit records")
        variance_raw = cast(float | int | str | None, payload.get("entailment_variance"))
        variance: float | None
        try:
            variance = None if variance_raw is None else float(variance_raw)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            variance = None

        instability_raw = payload.get("instability_flag")
        instability: bool | None
        if instability_raw is None:
            instability = None
        elif isinstance(instability_raw, bool):
            instability = instability_raw
        elif isinstance(instability_raw, (int, float)):
            instability = bool(instability_raw)
        else:
            instability = str(instability_raw).strip().lower() in {"true", "1", "yes"}

        sample_raw = cast(int | float | str | None, payload.get("sample_size"))
        sample_size: int | None
        try:
            sample_size = None if sample_raw is None else int(sample_raw)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            sample_size = None

        notes_value = payload.get("notes")
        if notes_value is None or isinstance(notes_value, str):
            notes = notes_value
        else:
            notes = str(notes_value)

        score_value = payload.get("entailment_score")
        if isinstance(score_value, (float, int)):
            score = float(score_value)
        elif isinstance(score_value, str):
            try:
                score = float(score_value)
            except ValueError:
                score = None
        else:
            score = None

        namespace_value = payload.get("namespace")
        namespace = str(namespace_value) if namespace_value not in (None, "") else None

        return cls(
            claim_id=claim_id,
            status=status,
            entailment_score=score,
            sources=serialised_sources,
            notes=notes,
            entailment_variance=variance,
            instability_flag=instability,
            sample_size=sample_size,
            provenance=provenance,
            audit_id=audit_id,
            created_at=created_at,
            namespace=namespace,
        )

    @classmethod
    def from_score(
        cls,
        claim_id: str,
        score: float | None,
        *,
        sources: Sequence[JSONMapping] | None = None,
        notes: str | None = None,
        status: ClaimAuditStatus | str | None = None,
        variance: float | None = None,
        instability: bool | None = None,
        sample_size: int | None = None,
        provenance: JSONMapping | None = None,
    ) -> "ClaimAuditRecord":
        """Build a record from an entailment score and optional metadata."""

        # ``provenance`` captures structured metadata describing how the
        # entailment decision was produced (e.g., retrieval queries or retries).

        resolved_status: ClaimAuditStatus
        if status is None:
            resolved_status = ClaimAuditStatus.from_entailment(score)
        elif isinstance(status, ClaimAuditStatus):
            resolved_status = status
        else:
            resolved_status = ClaimAuditStatus(str(status))

        serialised_sources: list[JSONDict] = []
        if sources:
            for src in sources:
                if isinstance(src, Mapping):
                    serialised_sources.append(to_json_dict(src))
                else:
                    raise TypeError("sources must contain mappings")

        if provenance is None:
            provenance_payload: JSONDict = {}
        elif isinstance(provenance, Mapping):
            provenance_payload = to_json_dict(provenance)
        else:
            raise TypeError("provenance must be a mapping")

        return cls(
            claim_id=claim_id,
            status=resolved_status,
            entailment_score=score,
            sources=serialised_sources,
            notes=notes,
            entailment_variance=variance,
            instability_flag=instability,
            sample_size=sample_size,
            provenance=provenance_payload,
        )


@dataclass(slots=True)
class WorkspaceResource:
    """Describe a single resource tracked within a workspace manifest."""

    resource_id: str
    kind: str
    reference: str
    citation_required: bool = True
    metadata: JSONDict = field(default_factory=dict)

    def to_payload(self) -> JSONDict:
        """Return a serialisable mapping for persistence layers."""

        return {
            "resource_id": self.resource_id,
            "kind": self.kind,
            "reference": self.reference,
            "citation_required": self.citation_required,
            "metadata": ensure_mutable_mapping(self.metadata),
        }

    @classmethod
    def from_payload(cls, payload: JSONMapping) -> "WorkspaceResource":
        """Construct a resource from persisted payload."""

        data = serialise_workspace_resource(payload)
        return cls(
            resource_id=str(data["resource_id"]),
            kind=str(data["kind"]),
            reference=str(data["reference"]),
            citation_required=bool(data.get("citation_required", True)),
            metadata=ensure_mutable_mapping(data.get("metadata", {})),
        )


@dataclass(slots=True)
class WorkspaceManifest:
    """Versioned collection of resources associated with a workspace."""

    workspace_id: str
    name: str
    version: int
    resources: list[WorkspaceResource] = field(default_factory=list)
    manifest_id: str = field(default_factory=lambda: str(uuid4()))
    parent_manifest_id: str | None = None
    created_at: float = field(default_factory=time.time)
    annotations: JSONDict = field(default_factory=dict)

    def to_payload(self) -> JSONDict:
        """Serialise the manifest for persistence."""

        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "version": int(self.version),
            "manifest_id": self.manifest_id,
            "parent_manifest_id": self.parent_manifest_id,
            "created_at": float(self.created_at),
            "resources": [resource.to_payload() for resource in self.resources],
            "annotations": ensure_mutable_mapping(self.annotations),
        }

    @classmethod
    def from_payload(cls, payload: JSONMapping) -> "WorkspaceManifest":
        """Return a manifest constructed from storage payload."""

        workspace_id_value = payload.get("workspace_id")
        if not workspace_id_value:
            raise StorageError("workspace_id is required for manifests")
        name_value = payload.get("name")
        if not name_value:
            raise StorageError("manifest name is required")
        version_value = payload.get("version")
        if version_value is None:
            raise StorageError("manifest version is required")
        try:
            version = int(version_value)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise StorageError("manifest version must be an integer") from exc
        manifest_id_value = payload.get("manifest_id") or str(uuid4())
        parent_value = payload.get("parent_manifest_id")
        created_raw = payload.get("created_at")
        created_at = float(created_raw) if created_raw is not None else time.time()
        annotations_raw = payload.get("annotations") or {}
        if isinstance(annotations_raw, Mapping):
            annotations = ensure_mutable_mapping(annotations_raw)
        else:
            raise StorageError("manifest annotations must be a mapping")
        resources_raw = payload.get("resources") or []
        if not isinstance(resources_raw, Sequence) or isinstance(resources_raw, (str, bytes)):
            raise StorageError("manifest resources must be a sequence")
        resources = [WorkspaceResource.from_payload(cast(JSONMapping, item)) for item in resources_raw]
        return cls(
            workspace_id=str(workspace_id_value),
            name=str(name_value),
            version=version,
            resources=resources,
            manifest_id=str(manifest_id_value),
            parent_manifest_id=str(parent_value) if parent_value else None,
            created_at=created_at,
            annotations=annotations,
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
    ctx.rdf_namespaces.clear()

    if _kuzu_backend is not None:
        try:
            _kuzu_backend.close()
        except Exception as exc:  # pragma: no cover - optional dependency
            log.warning("Failed to close Kuzu backend during reinit: %s", exc)
        _kuzu_backend = None

    ctx.graph = None
    ctx.kg_graph = None
    ctx.config_fingerprint = None


def set_message_queue(queue: "StorageQueueProtocol | None") -> None:
    """Configure a message queue for distributed persistence."""
    global _message_queue
    if queue is not None and not isinstance(queue, StorageQueueProtocol):
        raise TypeError("storage message queue must implement StorageQueueProtocol")
    _message_queue = queue


def set_delegate(delegate: StorageDelegateProtocol | None) -> None:
    """Replace StorageManager implementation globally."""
    global _delegate
    _delegate = delegate


def get_delegate() -> StorageDelegateProtocol | None:
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

        if ctx.graph is None:
            ctx.graph = nx.DiGraph()
        if ctx.kg_graph is None:
            ctx.kg_graph = nx.MultiDiGraph()

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

        if ctx.graph is None:
            ctx.graph = nx.DiGraph()
        if ctx.kg_graph is None:
            ctx.kg_graph = nx.MultiDiGraph()

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
        ctx.kg_graph = None
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
    def _namespace_settings() -> tuple[str, Mapping[str, str], Mapping[str, Any]]:
        cfg = ConfigLoader().config.storage
        namespaces_cfg = getattr(cfg, "namespaces", None)
        if namespaces_cfg is None:
            return DEFAULT_NAMESPACE_LABEL, {}, {}
        default_namespace = getattr(
            namespaces_cfg,
            "default_namespace",
            DEFAULT_NAMESPACE_LABEL,
        )
        routes = dict(getattr(namespaces_cfg, "routes", {}))
        merge_policies = dict(getattr(namespaces_cfg, "merge_policies", {}))
        return default_namespace, routes, merge_policies

    @staticmethod
    def _resolve_namespace_label(
        namespace: NamespaceTokens | Mapping[str, str] | str | None,
    ) -> str:
        default_namespace, routes, _ = StorageManager._namespace_settings()
        if isinstance(namespace, str):
            return canonical_namespace(namespace, default=default_namespace)
        tokens = NamespaceTokens.from_any(namespace)
        resolved = resolve_namespace(tokens, routes, default_namespace)
        return canonical_namespace(resolved, default=default_namespace)

    @staticmethod
    def _graph_node_id(namespace: str, claim_id: str) -> str:
        default_namespace, _, _ = StorageManager._namespace_settings()
        if namespace == default_namespace:
            return claim_id
        return f"{namespace}::{claim_id}"

    @staticmethod
    def _kg_node_id(namespace: str, entity_id: str) -> str:
        """Return a stable knowledge-graph node identifier scoped by namespace."""

        default_namespace, _, _ = StorageManager._namespace_settings()
        if namespace == default_namespace:
            return entity_id
        return f"{namespace}::{entity_id}"

    @staticmethod
    def _derive_namespace(
        namespace: NamespaceTokens | Mapping[str, str] | str | None,
        claim: JSONDict | None = None,
    ) -> str:
        candidate: NamespaceTokens | Mapping[str, str] | str | None = namespace
        if candidate is None and claim is not None:
            candidate = claim.get("namespace")
        return StorageManager._resolve_namespace_label(candidate)

    @staticmethod
    def _rdf_graph_for_namespace(namespace: str) -> GraphProtocol:
        StorageManager._ensure_storage_initialized()
        ctx = StorageManager.context
        if ctx.rdf_store is None:
            raise StorageError("RDF store not initialized")
        default_namespace, _, _ = StorageManager._namespace_settings()
        if namespace == default_namespace:
            return cast(GraphProtocol, ctx.rdf_store)
        existing = ctx.rdf_namespaces.get(namespace)
        if existing is not None:
            return existing
        cfg = ConfigLoader().config.storage
        base_path = cfg.rdf_path
        suffix = namespace_table_suffix(namespace)
        if os.path.isdir(base_path):
            ns_path = os.path.join(base_path, suffix)
        else:
            ns_path = f"{base_path}_{suffix}"
        graph = init_rdf_store(cfg.rdf_backend, ns_path)
        ctx.rdf_namespaces[namespace] = graph
        return graph

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
            _delegate.teardown(remove_db, ctx, st)
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
        audit: ClaimAuditRecord | JSONMapping,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> ClaimAuditRecord:
        """Persist a claim audit entry across storage backends."""

        if _delegate and _delegate is not StorageManager:
            return _delegate.record_claim_audit(audit, namespace)

        payload = (
            audit.to_payload() if isinstance(audit, ClaimAuditRecord) else to_json_dict(audit)
        )
        namespace_label = StorageManager._derive_namespace(namespace, payload)
        payload.setdefault("namespace", namespace_label)
        return StorageManager._persist_claim_audit_payload(payload, namespace_label)

    @staticmethod
    def list_claim_audits(
        claim_id: str | None = None,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> list[ClaimAuditRecord]:
        """Return persisted claim audits, optionally filtered by claim id."""

        if _delegate and _delegate is not StorageManager:
            return _delegate.list_claim_audits(claim_id, namespace)

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        namespace_label = None
        if namespace is not None:
            namespace_label = StorageManager._derive_namespace(namespace, None)
        payloads = StorageManager.context.db_backend.list_claim_audits(
            claim_id, namespace_label
        )
        return [ClaimAuditRecord.from_payload(p) for p in payloads]

    @staticmethod
    def save_workspace_manifest(
        manifest: WorkspaceManifest | JSONMapping,
        *,
        increment_version: bool = True,
    ) -> WorkspaceManifest:
        """Persist a workspace manifest version and return the stored record."""

        if _delegate and _delegate is not StorageManager:
            return _delegate.save_workspace_manifest(manifest, increment_version=increment_version)

        payload = manifest.to_payload() if isinstance(manifest, WorkspaceManifest) else to_json_dict(manifest)
        return StorageManager._persist_workspace_manifest_payload(
            payload,
            increment_version=increment_version,
        )

    @staticmethod
    def get_workspace_manifest(
        workspace_id: str,
        version: int | None = None,
        manifest_id: str | None = None,
    ) -> WorkspaceManifest:
        """Return a persisted manifest matching ``workspace_id`` and version."""

        if _delegate and _delegate is not StorageManager:
            return _delegate.get_workspace_manifest(workspace_id, version=version, manifest_id=manifest_id)

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        payload = StorageManager.context.db_backend.get_workspace_manifest(
            workspace_id,
            version,
            manifest_id,
        )
        if payload is None:
            raise NotFoundError(
                "Workspace manifest not found",
                resource_type="workspace_manifest",
                resource_id=workspace_id,
            )
        return WorkspaceManifest.from_payload(payload)

    @staticmethod
    def list_workspace_manifests(
        workspace_id: str | None = None,
    ) -> list[WorkspaceManifest]:
        """List manifests optionally scoped to a specific workspace."""

        if _delegate and _delegate is not StorageManager:
            return _delegate.list_workspace_manifests(workspace_id)

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        payloads = StorageManager.context.db_backend.list_workspace_manifests(workspace_id)
        return [WorkspaceManifest.from_payload(item) for item in payloads]

    @staticmethod
    def save_scholarly_paper(record: JSONMapping | Mapping[str, Any]) -> JSONDict:
        """Persist scholarly paper metadata and return the stored payload."""

        if _delegate and hasattr(_delegate, "save_scholarly_paper"):
            return cast(JSONDict, getattr(_delegate, "save_scholarly_paper")(record))

        payload = to_json_dict(record)
        namespace_value = payload.get("namespace")
        if not namespace_value:
            metadata_raw = payload.get("metadata") or {}
            if isinstance(metadata_raw, Mapping):
                identifier_raw = metadata_raw.get("identifier") or {}
                if isinstance(identifier_raw, Mapping):
                    namespace_value = identifier_raw.get("namespace")
        namespace_label = StorageManager._resolve_namespace_label(namespace_value)
        payload["namespace"] = namespace_label
        metadata_payload = payload.get("metadata")
        if isinstance(metadata_payload, Mapping):
            identifier_payload = metadata_payload.get("identifier")
            if isinstance(identifier_payload, Mapping):
                identifier_payload = dict(identifier_payload)
                identifier_payload["namespace"] = namespace_label
                metadata_payload = dict(metadata_payload)
                metadata_payload["identifier"] = identifier_payload
                payload["metadata"] = metadata_payload
        provider_value = str(payload.get("provider") or "").strip()
        paper_id_value = str(payload.get("paper_id") or "").strip()
        if not provider_value or not paper_id_value:
            raise StorageError("scholarly paper payload requires provider and paper_id")
        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        StorageManager.context.db_backend.persist_scholarly_paper(namespace_label, payload)
        return payload

    @staticmethod
    def list_scholarly_papers(
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
        provider: str | None = None,
    ) -> list[JSONDict]:
        """Return cached scholarly papers optionally filtered by provider."""

        if _delegate and hasattr(_delegate, "list_scholarly_papers"):
            return cast(
                list[JSONDict],
                getattr(_delegate, "list_scholarly_papers")(namespace, provider),
            )

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        namespace_label: str | None = None
        if namespace is not None:
            namespace_label = StorageManager._derive_namespace(namespace, None)
        return StorageManager.context.db_backend.list_scholarly_papers(namespace_label, provider)

    @staticmethod
    def get_scholarly_paper(
        namespace: NamespaceTokens | Mapping[str, str] | str,
        provider: str,
        paper_id: str,
    ) -> JSONDict:
        """Return a specific scholarly paper payload."""

        if _delegate and hasattr(_delegate, "get_scholarly_paper"):
            return cast(
                JSONDict,
                getattr(_delegate, "get_scholarly_paper")(namespace, provider, paper_id),
            )

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        namespace_label = StorageManager._derive_namespace(namespace, None)
        return StorageManager.context.db_backend.get_scholarly_paper(
            namespace_label,
            provider,
            paper_id,
        )

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

            vss_available = StorageManager.has_vss()

            def _compute_survivor_floor() -> int | None:
                if use_deterministic_budget:
                    assert target_node_count is not None
                    return max(target_node_count, minimum_resident_nodes)
                if policy == "lru" and vss_available:
                    return max(minimum_resident_nodes, _MIN_DETERMINISTIC_SURVIVORS)
                return None

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
                survivor_floor = _compute_survivor_floor()
                if use_deterministic_budget:
                    assert survivor_floor is not None
                    remaining_allowance = max(0, len(graph.nodes) - survivor_floor)
                    if remaining_allowance <= 0:
                        log.debug(
                            "Deterministic mode reached survivor floor (%d nodes); stopping",
                            survivor_floor,
                        )
                        break
                    current_batch_size = min(current_batch_size, remaining_allowance)

                nodes_to_evict: list[str] = []
                lru_mutated_in_iteration = False
                lru_node_enqueued = False

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
                                lru_mutated_in_iteration = True

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
                        if popped is not None:
                            lru_mutated_in_iteration = True
                        if popped and StorageManager.context.graph.has_node(popped):
                            nodes_to_evict.append(popped)
                            lru_node_enqueued = True
                else:
                    while len(nodes_to_evict) < current_batch_size and StorageManager.state.lru:
                        popped = StorageManager._pop_lru()
                        if popped and StorageManager.context.graph.has_node(popped):
                            nodes_to_evict.append(popped)
                            lru_mutated_in_iteration = True

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
                if policy == "lru" and lru_node_enqueued:
                    fallback_needed = False
                if fallback_needed:
                    missing = current_batch_size - len(nodes_to_evict)
                    if missing > 0:
                        fallback_allowance = missing
                        if remaining_allowance is not None:
                            fallback_allowance = min(
                                fallback_allowance,
                                max(0, remaining_allowance - len(nodes_to_evict)),
                            )

                        if survivor_floor is not None:
                            max_evictable = max(
                                0,
                                len(graph.nodes) - survivor_floor - len(nodes_to_evict),
                            )
                            fallback_allowance = min(fallback_allowance, max_evictable)

                        if fallback_allowance > 0:
                            fallback_candidates: list[str] = []
                            for node_id in list(graph.nodes):
                                if node_id in nodes_to_evict:
                                    continue
                                if not graph.has_node(node_id):
                                    continue
                                fallback_candidates.append(node_id)
                                if len(fallback_candidates) >= fallback_allowance:
                                    break
                            if fallback_candidates:
                                log.debug(
                                    "Eviction fallback selected %d graph nodes due to stale cache",
                                    len(fallback_candidates),
                                )
                            nodes_to_evict.extend(fallback_candidates)

                if lru_mutated_in_iteration and len(nodes_to_evict) > current_batch_size:
                    nodes_to_evict = nodes_to_evict[:current_batch_size]

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
    def _validate_claim(claim: JSONDict) -> None:
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
        if (
            StorageManager.context.db_backend is None
            or StorageManager.context.graph is None
            or StorageManager.context.kg_graph is None
        ):
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
        if StorageManager.context.kg_graph is None:
            raise StorageError(
                "Knowledge graph not initialized",
                suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations",
            )

    @staticmethod
    def _persist_to_networkx(claim: JSONDict, namespace: str) -> None:
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
            attributes_raw = claim.get("attributes")
            attrs = to_json_dict(attributes_raw) if isinstance(attributes_raw, Mapping) else {}
            if "confidence" in claim:
                attrs["confidence"] = claim["confidence"]
            if "audit" in claim:
                attrs["audit"] = claim["audit"]
            attrs["namespace"] = namespace
            attrs["id"] = claim.get("id")
            node_key = StorageManager._graph_node_id(namespace, str(claim.get("id", "")))
            assert StorageManager.context.graph is not None
            StorageManager.context.graph.add_node(node_key, **attrs)
            # Increment the counter and store it to maintain deterministic
            # ordering.  A re-entrant lock ensures concurrent writers cannot
            # race on the counter or LRU structure.
            state.lru_counter += 1
            state.lru[node_key] = state.lru_counter
            for rel in claim.get("relations", []):
                assert StorageManager.context.graph is not None
                src = StorageManager._graph_node_id(namespace, str(rel.get("src", "")))
                dst = StorageManager._graph_node_id(namespace, str(rel.get("dst", "")))
                StorageManager.context.graph.add_edge(
                    src,
                    dst,
                    **rel.get("attributes", {}),
                )

    @staticmethod
    def _persist_claim_audit_payload(
        audit_payload: JSONMapping, namespace: str
    ) -> ClaimAuditRecord:
        """Persist verification metadata across storage backends."""

        record = ClaimAuditRecord.from_payload(to_json_dict(audit_payload))
        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        payload = record.to_payload()
        payload["namespace"] = namespace
        StorageManager.context.db_backend.persist_claim_audit(payload, namespace)

        graph = StorageManager.context.graph
        node_key = StorageManager._graph_node_id(namespace, record.claim_id)
        if graph is not None and graph.has_node(node_key):
            graph.nodes[node_key]["audit"] = payload
        return record

    @staticmethod
    def _persist_workspace_manifest_payload(
        manifest_payload: JSONMapping,
        *,
        increment_version: bool,
    ) -> WorkspaceManifest:
        """Persist a workspace manifest and return the stored record."""

        StorageManager._ensure_storage_initialized()
        payload = to_json_dict(manifest_payload)

        name_value = str(payload.get("name") or "").strip()
        if not name_value:
            raise StorageError("workspace manifest requires a name")
        workspace_raw = str(payload.get("workspace_id") or "").strip()
        workspace_id = normalise_workspace_slug(workspace_raw or name_value)
        payload["workspace_id"] = workspace_id
        payload["name"] = name_value

        annotations_raw = payload.get("annotations") or {}
        if isinstance(annotations_raw, Mapping):
            payload["annotations"] = ensure_mutable_mapping(annotations_raw)
        else:
            raise StorageError("workspace manifest annotations must be a mapping")

        resources_raw = payload.get("resources") or []
        if not isinstance(resources_raw, Sequence) or isinstance(resources_raw, (str, bytes)):
            raise StorageError("workspace manifest resources must be a sequence")
        normalised_resources: list[JSONDict] = []
        for item in resources_raw:
            if isinstance(item, Mapping):
                normalised_resources.append(serialise_workspace_resource(item))
            else:
                raise StorageError("workspace manifest resources must be mappings")
        payload["resources"] = normalised_resources

        manifest_id_value = str(payload.get("manifest_id") or "").strip()
        if not manifest_id_value:
            manifest_id_value = str(uuid4())
        payload["manifest_id"] = manifest_id_value

        parent_raw = payload.get("parent_manifest_id")
        if parent_raw:
            parent_value = str(parent_raw).strip()
            payload["parent_manifest_id"] = parent_value or None
        else:
            payload["parent_manifest_id"] = None

        created_raw = payload.get("created_at")
        payload["created_at"] = float(created_raw) if created_raw is not None else time.time()

        version_raw = payload.get("version")
        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        if increment_version or version_raw is None:
            next_version = StorageManager.context.db_backend.next_workspace_manifest_version(workspace_id)
            payload["version"] = next_version
        else:
            try:
                payload["version"] = int(version_raw)
            except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
                raise StorageError("manifest version must be an integer") from exc

        StorageManager.context.db_backend.persist_workspace_manifest(payload)
        return WorkspaceManifest.from_payload(payload)

    @staticmethod
    def _persist_to_duckdb(claim: JSONDict) -> None:
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
    def _persist_to_kuzu(claim: JSONDict) -> None:
        """Persist a claim to the Kuzu graph database."""
        if _kuzu_backend is None:
            return
        _kuzu_backend.persist_claim(claim)

    @staticmethod
    def _persist_to_rdf(claim: JSONDict, namespace: str) -> None:
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
        rdf_store = cast(rdflib.Graph, StorageManager._rdf_graph_for_namespace(namespace))
        subj = rdflib.URIRef(f"urn:claim:{namespace}:{claim['id']}")
        for k, v in claim.get("attributes", {}).items():
            pred = rdflib.URIRef(f"urn:prop:{k}")
            obj = rdflib.Literal(v)
            graph_add(rdf_store, _as_rdf_triple(subj, pred, obj))

        # Apply ontology reasoning so advanced queries see inferred triples
        run_ontology_reasoner(rdf_store)

    @staticmethod
    def update_knowledge_graph(
        *,
        entities: Sequence[JSONMapping] | None = None,
        relations: Sequence[JSONMapping] | None = None,
        triples: Sequence[tuple[str, str, str]] | None = None,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> None:
        """Persist knowledge graph entities and relations across backends.

        Args:
            entities: Iterable of entity payloads produced by the knowledge
                graph pipeline.
            relations: Iterable of relation payloads mapping entity IDs via
                predicates.
            triples: Optional list of ``(subject, predicate, object)`` tuples
                used for RDF and analytics synchronisation.
            namespace: Optional namespace tokens controlling routing when
                payloads omit explicit namespace metadata.
        """

        if _delegate and _delegate is not StorageManager:
            return _delegate.update_knowledge_graph(
                entities=entities,
                relations=relations,
                triples=triples,
                namespace=namespace,
            )

        if not entities and not relations and not triples:
            return

        StorageManager._ensure_storage_initialized()

        fallback_namespace = StorageManager._resolve_namespace_label(namespace)
        entity_list: list[JSONDict] = [to_json_dict(item) for item in entities or []]
        relation_list: list[JSONDict] = [to_json_dict(item) for item in relations or []]

        grouped_entities: dict[str, list[JSONDict]] = defaultdict(list)
        grouped_relations: dict[str, list[JSONDict]] = defaultdict(list)
        entity_namespace_index: dict[str, str] = {}

        for entity in entity_list:
            ns_value = entity.get("namespace", fallback_namespace)
            entity_namespace = StorageManager._resolve_namespace_label(ns_value)
            entity_id = str(entity.get("id") or "")
            if not entity_id:
                continue
            attributes_raw = entity.get("attributes")
            attributes = (
                ensure_mutable_mapping(attributes_raw)
                if isinstance(attributes_raw, Mapping)
                else {}
            )
            entity["attributes"] = attributes
            entity["namespace"] = entity_namespace
            grouped_entities[entity_namespace].append(entity)
            entity_namespace_index[entity_id] = entity_namespace

        for relation in relation_list:
            ns_value = relation.get("namespace", fallback_namespace)
            relation_namespace = StorageManager._resolve_namespace_label(ns_value)
            subject_id = str(relation.get("subject_id") or "")
            object_id = str(relation.get("object_id") or "")
            if not subject_id or not object_id:
                continue
            predicate_raw = relation.get("predicate")
            predicate = str(predicate_raw) if predicate_raw else "related_to"
            provenance_raw = relation.get("provenance")
            provenance = (
                ensure_mutable_mapping(provenance_raw)
                if isinstance(provenance_raw, Mapping)
                else {}
            )
            try:
                weight = float(relation.get("weight", 1.0))
            except (TypeError, ValueError):
                weight = 1.0

            relation["subject_id"] = subject_id
            relation["object_id"] = object_id
            relation["predicate"] = predicate
            relation["provenance"] = provenance
            relation["weight"] = weight
            relation["namespace"] = relation_namespace

            grouped_relations[relation_namespace].append(relation)
            entity_namespace_index.setdefault(subject_id, relation_namespace)
            entity_namespace_index.setdefault(object_id, relation_namespace)

        triples_by_namespace: dict[str, list[RDFTriple]] = defaultdict(list)
        if triples:
            for subj_raw, pred_raw, obj_raw in triples:
                subject_id = str(subj_raw)
                object_id = str(obj_raw)
                predicate = str(pred_raw) if pred_raw else "related_to"
                ns_candidate = (
                    entity_namespace_index.get(subject_id)
                    or entity_namespace_index.get(object_id)
                    or fallback_namespace
                )
                namespace_label = StorageManager._resolve_namespace_label(ns_candidate)
                slug = namespace_table_suffix(namespace_label)
                triples_by_namespace[namespace_label].append(
                    _as_rdf_triple(
                        rdflib.URIRef(f"urn:kg:{slug}:{subject_id}"),
                        rdflib.URIRef(f"urn:kgp:{predicate}"),
                        rdflib.URIRef(f"urn:kg:{slug}:{object_id}"),
                    )
                )
        else:
            for namespace_label, ns_relations in grouped_relations.items():
                slug = namespace_table_suffix(namespace_label)
                for relation in ns_relations:
                    triples_by_namespace[namespace_label].append(
                        _as_rdf_triple(
                            rdflib.URIRef(f"urn:kg:{slug}:{relation['subject_id']}"),
                            rdflib.URIRef(f"urn:kgp:{relation['predicate']}"),
                            rdflib.URIRef(f"urn:kg:{slug}:{relation['object_id']}"),
                        )
                    )

        with StorageManager.state.lock():
            backend = StorageManager.context.db_backend
            kg_graph = StorageManager.context.kg_graph
            rdf_store = StorageManager.context.rdf_store

            if kg_graph is not None:
                for namespace_label, ns_entities in grouped_entities.items():
                    for entity in ns_entities:
                        entity_id = str(entity.get("id") or "")
                        if not entity_id:
                            continue
                        node_id = StorageManager._kg_node_id(namespace_label, entity_id)
                        attributes = dict(entity.get("attributes", {}))
                        attributes.setdefault("label", entity.get("label", entity_id))
                        attributes.setdefault("type", entity.get("type", "entity"))
                        if entity.get("source"):
                            attributes.setdefault("source", entity.get("source"))
                        attributes.setdefault("entity_id", entity_id)
                        attributes["namespace"] = namespace_label
                        kg_graph.add_node(node_id, **attributes)

                for namespace_label, ns_relations in grouped_relations.items():
                    for relation in ns_relations:
                        src_id = StorageManager._kg_node_id(
                            namespace_label, relation["subject_id"]
                        )
                        dst_id = StorageManager._kg_node_id(
                            namespace_label, relation["object_id"]
                        )
                        provenance_attrs = dict(relation.get("provenance", {}))
                        provenance_attrs["namespace"] = namespace_label
                        kg_graph.add_edge(
                            src_id,
                            dst_id,
                            key=relation["predicate"],
                            predicate=relation["predicate"],
                            weight=relation["weight"],
                            namespace=namespace_label,
                            **provenance_attrs,
                        )

            if backend is not None:
                for namespace_label, ns_entities in grouped_entities.items():
                    backend.persist_graph_entities(ns_entities, namespace_label)
                for namespace_label, ns_relations in grouped_relations.items():
                    backend.persist_graph_relations(ns_relations, namespace_label)

            if rdf_store is not None:
                for namespace_label, ns_triples in triples_by_namespace.items():
                    if not ns_triples:
                        continue
                    rdf_graph = cast(
                        rdflib.Graph, StorageManager._rdf_graph_for_namespace(namespace_label)
                    )
                    for triple in ns_triples:
                        graph_add(rdf_graph, triple)

                    try:
                        run_ontology_reasoner(rdf_graph)
                    except StorageError:
                        log.debug(
                            "Ontology reasoning skipped for knowledge graph update", exc_info=True
                        )

    @staticmethod
    def merge_claim_groups(
        claims_by_namespace: Mapping[str, Sequence[JSONMapping]],
        policy: str | NamespaceMergeConfig | None = None,
    ) -> list[JSONDict]:
        """Merge claim collections across namespaces using configured policies."""

        if not claims_by_namespace:
            return []

        if _delegate and _delegate is not StorageManager:
            merger = getattr(_delegate, "merge_claim_groups", None)
            if merger is not None:
                return merger(claims_by_namespace, policy)

        merge_config = StorageManager._resolve_merge_policy(policy)
        grouped = StorageManager._normalise_claim_groups(claims_by_namespace)
        if not grouped:
            return []

        if merge_config.strategy == NamespaceMergeStrategy.CONFIDENCE_WEIGHT:
            return StorageManager._merge_claims_confidence(grouped, merge_config.weights)
        return StorageManager._merge_claims_union(grouped)

    @staticmethod
    def _resolve_merge_policy(
        policy: str | NamespaceMergeConfig | None,
    ) -> NamespaceMergeConfig:
        if isinstance(policy, NamespaceMergeConfig):
            return policy
        _, _, merge_policies = StorageManager._namespace_settings()
        if isinstance(policy, str):
            config = merge_policies.get(policy)
            if isinstance(config, NamespaceMergeConfig):
                return config
            raise StorageError(f"Unknown namespace merge policy: {policy}")
        default_policy = merge_policies.get("default")
        if isinstance(default_policy, NamespaceMergeConfig):
            return default_policy
        return NamespaceMergeConfig()

    @staticmethod
    def _normalise_claim_groups(
        claims_by_namespace: Mapping[str, Sequence[JSONMapping]],
    ) -> dict[str, list[JSONDict]]:
        grouped: dict[str, list[JSONDict]] = {}
        for namespace, claims in claims_by_namespace.items():
            namespace_label = StorageManager._resolve_namespace_label(namespace)
            bucket = grouped.setdefault(namespace_label, [])
            for claim in claims:
                payload = to_json_dict(claim)
                payload.setdefault("namespace", namespace_label)
                bucket.append(payload)
        return grouped

    @staticmethod
    def _merge_claims_union(
        grouped: Mapping[str, Sequence[JSONDict]],
    ) -> list[JSONDict]:
        merged: dict[str, JSONDict] = {}
        provenance: dict[str, set[str]] = defaultdict(set)
        for namespace_label, claims in grouped.items():
            for claim in claims:
                claim_id = str(claim.get("id") or "")
                if not claim_id:
                    continue
                confidence = float(claim.get("confidence", 0.0) or 0.0)
                existing = merged.get(claim_id)
                if existing is None or confidence > float(existing.get("confidence", 0.0) or 0.0):
                    merged[claim_id] = dict(claim)
                provenance[claim_id].add(namespace_label)
        results: list[JSONDict] = []
        for claim_id, payload in merged.items():
            entry = dict(payload)
            namespaces = provenance.get(claim_id) or {entry.get("namespace", DEFAULT_NAMESPACE_LABEL)}
            entry["namespaces"] = sorted(namespaces)
            results.append(entry)
        return results

    @staticmethod
    def _merge_claims_confidence(
        grouped: Mapping[str, Sequence[JSONDict]],
        weights: Mapping[str, float],
    ) -> list[JSONDict]:
        normalised_weights = {
            StorageManager._resolve_namespace_label(key): float(value)
            for key, value in weights.items()
        }
        totals: dict[str, float] = defaultdict(float)
        weight_totals: dict[str, float] = defaultdict(float)
        provenance: dict[str, set[str]] = defaultdict(set)
        best_sources: dict[str, JSONDict] = {}
        best_weight: dict[str, float] = defaultdict(float)
        for namespace_label, claims in grouped.items():
            weight = normalised_weights.get(namespace_label, 1.0)
            if weight <= 0:
                continue
            for claim in claims:
                claim_id = str(claim.get("id") or "")
                if not claim_id:
                    continue
                provenance[claim_id].add(namespace_label)
                confidence = float(claim.get("confidence", 0.0) or 0.0)
                totals[claim_id] += confidence * weight
                weight_totals[claim_id] += weight
                if weight >= best_weight.get(claim_id, float("-inf")):
                    best_weight[claim_id] = weight
                    best_sources[claim_id] = dict(claim)
        results: list[JSONDict] = []
        for claim_id, payload in best_sources.items():
            entry = dict(payload)
            total_weight = weight_totals.get(claim_id, 0.0)
            if total_weight > 0:
                confidence = totals[claim_id] / total_weight
                entry["confidence"] = max(0.0, min(1.0, confidence))
            entry["namespaces"] = sorted(provenance.get(claim_id, set()))
            results.append(entry)
        return results

    def persist_claim(
        claim: JSONDict,
        partial_update: bool = False,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> None:
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

        namespace_label = StorageManager._derive_namespace(namespace, claim)

        if _message_queue is not None:
            _message_queue.put(
                _persist_claim_message(claim, partial_update, namespace_label)
            )
            return

        # Validate claim
        StorageManager._validate_claim(claim)

        with StorageManager.state.lock:
            # Ensure storage is initialized
            StorageManager._ensure_storage_initialized()

            # Check if this is an update to an existing claim
            claim_id = claim["id"]
            node_key = StorageManager._graph_node_id(namespace_label, claim_id)
            existing_claim = None
            is_update = False

            # Track timing for performance metrics
            import time

            start_time = time.time()

            # Check if the claim already exists in the graph
            assert StorageManager.context.graph is not None
            if StorageManager.context.graph.has_node(node_key):
                is_update = True
                if partial_update:
                    # Get the existing claim data
                    existing_claim = dict(StorageManager.context.graph.nodes[node_key])

                    # Merge the new claim data with the existing data
                    # Note: We're careful not to modify the input claim
                    merged_claim = dict(existing_claim)

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
            claim_to_persist["namespace"] = namespace_label
            StorageManager._persist_to_networkx(claim_to_persist, namespace_label)

            audit_payload = claim_to_persist.get("audit")
            if audit_payload:
                if isinstance(audit_payload, ClaimAuditRecord):
                    payload = audit_payload.to_payload()
                elif isinstance(audit_payload, Mapping):
                    payload = to_json_dict(audit_payload)
                else:
                    payload = None
                if payload is not None:
                    payload.setdefault("claim_id", claim_id)
                    StorageManager._persist_claim_audit_payload(payload, namespace_label)

            # For database backends, use different methods for updates vs. new claims
            assert StorageManager.context.db_backend is not None
            if is_update:
                # Update existing records
                StorageManager.context.db_backend.update_claim(
                    claim_to_persist, partial_update, namespace_label
                )
                StorageManager._update_rdf_claim(
                    claim_to_persist, namespace_label, partial_update
                )
                StorageManager._persist_to_kuzu(claim_to_persist)
            else:
                # Insert new records
                StorageManager.context.db_backend.persist_claim(
                    claim_to_persist, namespace_label
                )
                StorageManager._persist_to_rdf(claim_to_persist, namespace_label)
                StorageManager._persist_to_kuzu(claim_to_persist)

            # Refresh vector index if embeddings were provided
            if claim.get("embedding") is not None and StorageManager.has_vss():
                try:
                    StorageManager.refresh_vector_index()
                except Exception as e:
                    log.warning(f"Failed to refresh vector index: {e}")

            # Update LRU cache to mark this claim as recently used
            StorageManager.touch_node(claim_id, namespace_label)

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
    def update_claim(
        claim: JSONDict,
        partial_update: bool = False,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> None:
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

        namespace_label = StorageManager._derive_namespace(namespace, claim)

        if _message_queue is not None:
            _message_queue.put(
                _persist_claim_message(claim, partial_update, namespace_label)
            )
            return

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        StorageManager.context.db_backend.update_claim(
            claim, partial_update, namespace_label
        )

        audit_payload = claim.get("audit")
        if audit_payload:
            if isinstance(audit_payload, ClaimAuditRecord):
                payload = audit_payload.to_payload()
            elif isinstance(audit_payload, Mapping):
                payload = to_json_dict(audit_payload)
            else:
                payload = None
            if payload is not None:
                payload.setdefault("claim_id", claim.get("id", ""))
                if payload.get("claim_id"):
                    StorageManager._persist_claim_audit_payload(payload, namespace_label)

    @staticmethod
    def get_claim(
        claim_id: str,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> JSONDict:
        """Retrieve a persisted claim from DuckDB."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.get_claim(claim_id, namespace)

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        namespace_label = StorageManager._derive_namespace(namespace, None)
        claim = StorageManager.context.db_backend.get_claim(
            claim_id, namespace_label
        )
        claim.setdefault("namespace", namespace_label)
        return claim

    @staticmethod
    def _update_rdf_claim(
        claim: JSONDict, namespace: str, partial_update: bool = False
    ) -> None:
        """Update an existing claim in the RDF store.

        This method updates an existing claim in the RDF store, either by completely
        replacing it or by merging new data with existing data.

        Args:
            claim: The claim to update
            partial_update: If True, merge with existing data rather than replacing
        """
        assert StorageManager.context.rdf_store is not None
        subj = rdflib.URIRef(f"urn:claim:{namespace}:{claim['id']}")

        rdf_store = cast(rdflib.Graph, StorageManager._rdf_graph_for_namespace(namespace))

        if not partial_update:
            # Remove all existing triples for this subject
            pattern = cast(RDFTriplePattern, (subj, None, None))
            for s, p, o in graph_triples(rdf_store, pattern):
                rdf_store.remove((s, p, o))

        # Add new triples
        for k, v in claim.get("attributes", {}).items():
            pred = rdflib.URIRef(f"urn:prop:{k}")
            obj = rdflib.Literal(v)
            graph_add(rdf_store, _as_rdf_triple(subj, pred, obj))
        # Apply ontology reasoning so updates expose inferred triples
        run_ontology_reasoner(rdf_store)

    @staticmethod
    def update_rdf_claim(
        claim: JSONDict,
        partial_update: bool = False,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> None:
        """Public wrapper around :func:`_update_rdf_claim`."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.update_rdf_claim(claim, partial_update, namespace)

        StorageManager._ensure_storage_initialized()
        namespace_label = StorageManager._derive_namespace(namespace, claim)
        StorageManager._update_rdf_claim(claim, namespace_label, partial_update)

    @staticmethod
    def create_hnsw_index(
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> None:
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
            return _delegate.create_hnsw_index(namespace)

        # Ensure storage is initialized
        if StorageManager.context.db_backend is None:
            setup(context=StorageManager.context, state=StorageManager.state)
        assert StorageManager.context.db_backend is not None

        # Use the DuckDBStorageBackend to create the HNSW index
        try:
            namespace_label = StorageManager._derive_namespace(namespace, None)
            StorageManager.context.db_backend.create_hnsw_index(namespace_label)
        except Exception as e:
            raise StorageError("Failed to create HNSW index", cause=e)

    @staticmethod
    def refresh_vector_index(
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> None:
        """Rebuild the vector index to include new embeddings."""
        if _delegate and _delegate is not StorageManager:
            return _delegate.refresh_vector_index(namespace)

        StorageManager._ensure_storage_initialized()
        assert StorageManager.context.db_backend is not None
        try:
            namespace_label = StorageManager._derive_namespace(namespace, None)
            StorageManager.context.db_backend.refresh_hnsw_index(namespace_label)
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
    def vector_search(
        query_embedding: list[float],
        k: int = 5,
        namespace: NamespaceTokens | Mapping[str, str] | str | None = None,
    ) -> JSONDictList:
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
            return _delegate.vector_search(query_embedding, k, namespace)

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
            namespace_label = StorageManager._derive_namespace(namespace, None)
            results = db_backend.vector_search(query_embedding, k, namespace_label)
            for item in results:
                item.setdefault("namespace", namespace_label)
            return results
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
    def get_knowledge_graph(create: bool = True) -> nx.MultiDiGraph[Any] | None:
        """Return the multi-relational knowledge graph used for reasoning.

        Args:
            create: When ``True`` initialise storage components if required.

        Returns:
            The in-memory :class:`networkx.MultiDiGraph` backing the knowledge
            graph, or ``None`` when ``create`` is ``False`` and the graph has
            not been initialised.

        Raises:
            NotFoundError: If initialisation fails or the graph remains
                unavailable when ``create`` is ``True``.
        """

        if _delegate and _delegate is not StorageManager:
            getter = cast(
                Callable[[bool], nx.MultiDiGraph[Any] | None] | None,
                getattr(_delegate, "get_knowledge_graph", None),
            )
            if getter is not None:
                return getter(create)

        state = StorageManager.state
        with state.lock:
            context = state.context
            kg_graph_opt = context.kg_graph
            if kg_graph_opt is None and create:
                try:
                    setup(context=context, state=StorageManager.state)
                except Exception as exc:
                    raise NotFoundError("Knowledge graph not initialized", cause=exc)
            kg_graph_opt = context.kg_graph
            if kg_graph_opt is None:
                if create:
                    raise NotFoundError("Knowledge graph not initialized")
                return None
            return kg_graph_opt

    @staticmethod
    def export_knowledge_graph_graphml() -> str:
        """Serialise the knowledge graph into GraphML.

        Returns:
            GraphML text describing the current knowledge graph, or an empty
            string when the graph is unavailable.
        """

        graph = StorageManager.get_knowledge_graph(create=False)
        if graph is None or not graph.nodes:
            return ""
        return "\n".join(list(nx.generate_graphml(graph)))

    @staticmethod
    def export_knowledge_graph_json() -> str:
        """Serialise the knowledge graph into node-link JSON.

        Returns:
            JSON string containing the node-link representation of the current
            knowledge graph. Returns ``"{}"`` when the graph is unavailable.
        """

        graph = StorageManager.get_knowledge_graph(create=False)
        if graph is None or not graph.nodes:
            return "{}"
        payload = json_graph.node_link_data(graph, edges="edges")  # type: ignore[call-arg]
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def touch_node(node_id: str, namespace: str | None = None) -> None:
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
            return _delegate.touch_node(node_id, namespace)
        state = StorageManager.state
        lru = state.lru
        if namespace is not None:
            graph_key = StorageManager._graph_node_id(namespace, node_id)
        elif "::" in node_id:
            graph_key = node_id
        else:
            default_namespace, _, _ = StorageManager._namespace_settings()
            graph_key = StorageManager._graph_node_id(default_namespace, node_id)
        with state.lock:
            state.lru_counter += 1
            lru[graph_key] = state.lru_counter
            # ``move_to_end`` maintains the deque order for faster popping
            lru.move_to_end(graph_key)
            StorageManager._access_frequency[graph_key] = (
                StorageManager._access_frequency.get(graph_key, 0) + 1
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
            return cast(rdflib.Graph, StorageManager.context.rdf_store)

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
        backend_handle = cast(Any, store).store
        identifier = getattr(backend_handle, "identifier", backend_handle.__class__.__name__)
        return str(identifier)

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
        backend_handle = cast(Any, store).store
        actual_backend = str(
            getattr(backend_handle, "identifier", backend_handle.__class__.__name__)
        ).lower()
        if configured_backend == "memory" and actual_backend not in {"memory", "iomemory"}:
            preserved_triples = list(graph_triples(store, (None, None, None)))
            preserved_namespaces = list(cast(Any, store).namespaces())
            with StorageManager.state.lock:
                _reset_context(StorageManager.context)
                setup(context=StorageManager.context, state=StorageManager.state)
                restored = StorageManager.context.rdf_store or StorageManager.get_rdf_store()
                rdf_store = cast(rdflib.Graph, restored)
                for prefix, namespace in preserved_namespaces:
                    try:
                        cast(Any, rdf_store).bind(prefix, namespace, override=True)
                    except Exception:  # pragma: no cover - namespace restoration best-effort
                        log.debug("Failed to restore namespace binding", exc_info=True)
                for triple in preserved_triples:
                    graph_add(rdf_store, triple)
                store = rdf_store
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
