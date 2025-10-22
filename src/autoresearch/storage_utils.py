"""Utility helpers for storage routines."""

from __future__ import annotations

from collections.abc import Iterator
import hashlib
import re
from typing import Any, Mapping, cast

from rdflib import Graph
from rdflib.term import Node as RDFNode

from .errors import StorageError
from .logging_utils import get_logger
from .storage_typing import JSONDict, RDFTriple, RDFTriplePattern, to_json_dict

log = get_logger(__name__)


def initialize_schema_version_without_fetchone(conn: Any) -> None:
    """Ensure the schema version exists in the metadata table.

    DuckDB cursors may lack :meth:`fetchone`, so this helper relies on
    :meth:`fetchall` to read existing values. If no version is present, it
    inserts ``1``.

    Args:
        conn: Active DuckDB connection.

    Raises:
        StorageError: If the schema version cannot be initialised.
    """
    try:
        execute_cls = getattr(conn.__class__, "execute", None)
        if execute_cls is not None:
            cursor = execute_cls(conn, "SELECT value FROM metadata WHERE key = 'schema_version'")
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
    """Return a deterministic slug for workspace identifiers.

    Args:
        name: Human readable workspace name.

    Returns:
        Lowercase slug composed of alphanumerics and hyphens.
    """

    if not name:
        raise StorageError("workspace name cannot be empty")

    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    slug = slug.strip("-")
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
