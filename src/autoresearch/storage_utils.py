"""Storage helper utilities shared across DuckDB and RDF backends."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator, Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, cast

from rdflib import Graph
from rdflib.term import Node as RDFNode

from .errors import StorageError
from .logging_utils import get_logger
from .storage_typing import JSONDict, RDFTriple, RDFTriplePattern, to_json_dict

log = get_logger(__name__)

DEFAULT_NAMESPACE_LABEL = "__default__"
_SCOPE_ORDER = ("session", "workspace", "org", "project")


@dataclass(frozen=True)
class NamespaceTokens:
    """Structured namespace tokens resolved from runtime context."""

    session: str | None = None
    workspace: str | None = None
    org: str | None = None
    project: str | None = None

    @classmethod
    def from_any(
        cls, value: "NamespaceTokens | str | Mapping[str, str] | None"
    ) -> "NamespaceTokens":
        """Return canonical tokens from ``value``.

        Strings are treated as explicit project-level namespaces, bypassing
        policy routing. Mappings are normalised by lowercasing recognised keys
        and discarding unknown scopes.
        """

        if isinstance(value, NamespaceTokens):
            return value
        if value is None:
            return cls()
        if isinstance(value, str):
            return cls(project=value)
        scopes: MutableMapping[str, str | None] = {scope: None for scope in _SCOPE_ORDER}
        for key, raw in value.items():
            lowered = str(key).strip().lower()
            if lowered in scopes and isinstance(raw, str):
                scopes[lowered] = raw
        return cls(
            session=scopes["session"],
            workspace=scopes["workspace"],
            org=scopes["org"],
            project=scopes["project"],
        )

    def get(self, scope: str) -> str | None:
        """Return the token associated with ``scope`` if present."""

        return getattr(self, scope, None)

    def as_dict(self) -> dict[str, str]:
        """Return a dictionary excluding empty scopes."""

        return {scope: value for scope in _SCOPE_ORDER if (value := self.get(scope))}


def canonical_namespace(namespace: str | None, *, default: str = DEFAULT_NAMESPACE_LABEL) -> str:
    """Return a canonical namespace label enforcing non-empty fallbacks."""

    candidate = (namespace or "").strip()
    return candidate or default


def namespace_table_suffix(namespace: str) -> str:
    """Return a DuckDB-safe suffix for ``namespace`` table derivations."""

    slug = re.sub(r"[^a-z0-9]+", "_", namespace.lower()).strip("_")
    if not slug:
        slug = "default"
    return slug[:48]


def validate_namespace_routes(routes: Mapping[str, str]) -> Mapping[str, str]:
    """Validate namespace routing policies, raising on cycles or unknown scopes."""

    allowed = set(_SCOPE_ORDER) | {"self"}
    for source, target in routes.items():
        if source not in _SCOPE_ORDER:
            raise StorageError(f"Unknown namespace scope: {source}")
        if target not in allowed:
            raise StorageError(f"Invalid namespace target {target!r} for scope {source!r}")
    for scope in _SCOPE_ORDER:
        seen: set[str] = set()
        current = scope
        while True:
            if current in seen:
                raise StorageError("Namespace routing contains a cycle")
            seen.add(current)
            target = routes.get(current)
            if target is None or target == "self" or target == "project":
                break
            current = target
    return routes


def _follow_route(scope: str, routes: Mapping[str, str]) -> list[str]:
    path = [scope]
    current = scope
    while True:
        target = routes.get(current)
        if target is None or target == "self":
            break
        path.append(target)
        if target == "project":
            break
        current = target
    return path


def resolve_namespace(
    tokens: NamespaceTokens,
    routes: Mapping[str, str],
    default_namespace: str = DEFAULT_NAMESPACE_LABEL,
) -> str:
    """Resolve the storage namespace using ``routes`` and ``tokens``."""

    validated = validate_namespace_routes(routes)
    for scope in _SCOPE_ORDER:
        token = tokens.get(scope)
        if not token:
            continue
        path = _follow_route(scope, validated)
        for candidate_scope in reversed(path):
            candidate = tokens.get(candidate_scope)
            if candidate:
                return candidate
        return token
    return canonical_namespace(tokens.project, default=default_namespace)


def initialize_schema_version_without_fetchone(conn: Any) -> None:
    """Ensure the schema version exists in the metadata table."""

    try:
        execute_cls = getattr(conn.__class__, "execute", None)
        if execute_cls is not None:
            cursor = execute_cls(
                conn, "SELECT value FROM metadata WHERE key = 'schema_version'"
            )
        else:
            cursor = conn.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'",
            )
        rows = cursor.fetchall() if hasattr(cursor, "fetchall") else []
        if not isinstance(rows, list) or not rows:
            log.info("Initializing schema version to 1")
            if execute_cls is not None:
                execute_cls(
                    conn,
                    "INSERT INTO metadata (key, value) VALUES ('schema_version', '1')",
                )
            else:
                conn.execute(
                    "INSERT INTO metadata (key, value) VALUES ('schema_version', '1')",
                )
    except Exception as exc:  # pragma: no cover - defensive
        raise StorageError("Failed to initialize schema version", cause=exc)


# Backward compatibility alias
initialize_schema_version = initialize_schema_version_without_fetchone


def ensure_rdf_node(value: RDFNode | None) -> RDFNode | None:
    """Return *value* unchanged while preserving optional ``RDFNode`` typing."""

    return value


def graph_triples(graph: Graph, pattern: RDFTriplePattern) -> Iterator[RDFTriple]:
    """Yield triples from *graph* with properly typed ``rdflib`` nodes."""

    return graph.triples(
        (
            ensure_rdf_node(pattern[0]),
            ensure_rdf_node(pattern[1]),
            ensure_rdf_node(pattern[2]),
        )
    )


def graph_add(graph: Graph, triple: RDFTriple) -> None:
    """Add *triple* to *graph* ensuring node compatibility."""

    graph.add(triple)


def graph_subject_objects(
    graph: Graph, predicate: RDFNode | str
) -> Iterator[tuple[RDFNode, RDFNode]]:
    """Iterate over subject/object pairs for *predicate* with node typing."""

    return graph.subject_objects(cast(RDFNode, predicate))


def normalise_workspace_slug(name: str) -> str:
    """Return a deterministic slug for workspace identifiers."""

    if not name:
        raise StorageError("workspace name cannot be empty")

    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise StorageError("workspace name must contain alphanumeric characters")
    return slug


def ensure_workspace_resource_id(kind: str, reference: str) -> str:
    """Return a stable identifier for workspace resources."""

    fingerprint = f"{kind}|{reference}".encode("utf-8", "ignore")
    digest = hashlib.sha256(fingerprint).hexdigest()[:12]
    return f"wsres-{digest}"


def serialise_workspace_resource(resource: Mapping[str, Any]) -> JSONDict:
    """Return a JSON-serialisable resource mapping with derived identifiers."""

    payload = to_json_dict(resource)
    kind = str(payload.get("kind") or payload.get("type") or "").strip().lower()
    reference = str(payload.get("reference") or payload.get("path") or "").strip()
    if not kind or not reference:
        raise StorageError("workspace resources require both kind and reference")

    resource_id = str(payload.get("resource_id") or "")
    if not resource_id:
        resource_id = ensure_workspace_resource_id(kind, reference)
    payload["resource_id"] = resource_id
    payload["kind"] = kind
    payload["reference"] = reference
    citation_required = payload.get("citation_required", True)
    payload["citation_required"] = bool(citation_required)
    metadata = payload.get("metadata")
    if isinstance(metadata, Mapping):
        payload["metadata"] = to_json_dict(metadata)
    elif metadata is None:
        payload["metadata"] = {}
    else:
        raise StorageError("workspace resource metadata must be a mapping")
    return payload
