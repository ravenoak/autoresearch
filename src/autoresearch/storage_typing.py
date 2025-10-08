"""Typed protocols and helpers for storage backends.

This module centralises protocol definitions for the storage layer so the
manager and backend implementations can interact with third-party libraries
through typed interfaces. The project depends on ``duckdb`` and ``rdflib``
which expose dynamically typed objects. By funnelling access through the
helpers in this module we avoid sprinkling ``Any`` throughout the codebase
while still delegating to the real implementations at runtime.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Iterator,
    Mapping,
    MutableMapping,
    Protocol,
    Sequence,
    TypeVar,
    cast,
)
from typing import runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    import duckdb
    import kuzu
    import rdflib
    from rdflib.query import Result as RDFQueryResult
    from rdflib.term import Node as RDFNode

else:  # pragma: no cover - executed only at runtime
    RDFNode = Any  # type: ignore[assignment]
    RDFQueryResult = Any  # type: ignore[assignment]


JSONValue = Any
JSONMapping = Mapping[str, JSONValue]
JSONDict = dict[str, JSONValue]
JSONDictList = list[JSONDict]

RDFTriple = tuple[RDFNode, RDFNode, RDFNode]
RDFTriplePattern = tuple[RDFNode | None, RDFNode | None, RDFNode | None]


@runtime_checkable
class RDFQueryResultProtocol(Protocol):
    """Protocol describing the subset of ``rdflib`` query results we consume."""

    bindings: Sequence[Mapping[str, JSONValue]]

    def __iter__(self) -> Iterator[Mapping[str, JSONValue]]:
        ...


@runtime_checkable
class GraphProtocol(Protocol):
    """Protocol capturing the required operations on an RDF graph."""

    def add(self, triple: RDFTriple) -> None:
        ...

    def remove(self, triple: RDFTriplePattern) -> None:
        ...

    def triples(self, triple_pattern: RDFTriplePattern) -> Iterator[RDFTriple]:
        ...

    def serialize(
        self,
        destination: str | None = None,
        format: str | None = None,
    ) -> bytes | None:
        ...

    def parse(
        self,
        source: str,
        publicID: str | None = None,
        format: str | None = None,
    ) -> GraphProtocol:
        ...

    def query(self, query: str) -> RDFQueryResultProtocol:
        ...

    def close(self) -> None:
        ...

    def __len__(self) -> int:
        ...


@runtime_checkable
class DuckDBCursorProtocol(Protocol):
    """Protocol describing the methods called on DuckDB cursors."""

    def execute(
        self,
        query: str,
        parameters: Sequence[JSONValue] | Mapping[str, JSONValue] | None = None,
    ) -> DuckDBCursorProtocol:
        ...

    def fetchall(self) -> list[tuple[JSONValue, ...]]:
        ...

    def fetchone(self) -> tuple[JSONValue, ...] | None:
        ...


@runtime_checkable
class DuckDBConnectionProtocol(Protocol):
    """Protocol for the subset of DuckDB connection methods we use."""

    def execute(
        self,
        query: str,
        parameters: Sequence[JSONValue] | Mapping[str, JSONValue] | None = None,
    ) -> DuckDBCursorProtocol:
        ...

    def close(self) -> None:
        ...


@runtime_checkable
class KuzuConnectionProtocol(Protocol):
    """Protocol describing the optional Kuzu connection interface."""

    def execute(
        self,
        query: str,
        params: Mapping[str, JSONValue] | None = None,
    ) -> Any:
        ...

    def close(self) -> None:
        ...


TMapping = TypeVar("TMapping", bound=Mapping[str, JSONValue])


def to_json_dict(mapping: TMapping | JSONDict | None) -> JSONDict:
    """Clone *mapping* into a standard ``dict`` with string keys."""

    if mapping is None:
        return {}
    if isinstance(mapping, dict):
        return dict(mapping)
    return {key: mapping[key] for key in mapping}


def ensure_mutable_mapping(mapping: Mapping[str, JSONValue]) -> MutableMapping[str, JSONValue]:
    """Return a mutable copy of ``mapping`` for in-place updates."""

    return dict(mapping)


def as_graph_protocol(graph: "rdflib.Graph") -> GraphProtocol:
    """Cast an ``rdflib.Graph`` to :class:`GraphProtocol` for type-checking."""

    return cast(GraphProtocol, graph)


def as_duckdb_connection(
    connection: "duckdb.DuckDBPyConnection",
) -> DuckDBConnectionProtocol:
    """Cast a DuckDB connection to :class:`DuckDBConnectionProtocol`."""

    return cast(DuckDBConnectionProtocol, connection)


def as_kuzu_connection(connection: "kuzu.Connection") -> KuzuConnectionProtocol:
    """Cast a Kuzu connection to :class:`KuzuConnectionProtocol`."""

    return cast(KuzuConnectionProtocol, connection)


__all__ = [
    "GraphProtocol",
    "DuckDBConnectionProtocol",
    "DuckDBCursorProtocol",
    "KuzuConnectionProtocol",
    "JSONDict",
    "JSONDictList",
    "JSONMapping",
    "JSONValue",
    "RDFQueryResultProtocol",
    "RDFTriple",
    "RDFTriplePattern",
    "as_duckdb_connection",
    "as_graph_protocol",
    "as_kuzu_connection",
    "ensure_mutable_mapping",
    "to_json_dict",
]
