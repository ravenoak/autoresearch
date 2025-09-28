from __future__ import annotations

from typing import Any, Iterable, Iterator, Optional

from . import exceptions, plugin, query, term

Node = term.Node


class URIRef(str): ...


class Literal(str): ...


class BNode(str): ...


class _Namespace:
    def __getattr__(self, name: str) -> URIRef: ...


RDF: _Namespace
RDFS: _Namespace
OWL: _Namespace


class Graph:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def add(self, triple: tuple[Node, Node, Node]) -> None: ...

    def remove(self, triple: tuple[Node | None, Node | None, Node | None]) -> None: ...

    def triples(self, pattern: tuple[Node | None, Node | None, Node | None]) -> Iterator[tuple[Node, Node, Node]]: ...

    def subject_objects(self, predicate: Node) -> Iterator[tuple[Node, Node]]: ...

    def objects(self, subject: Node, predicate: Node) -> Iterator[Node]: ...

    def query(self, query: str) -> query.Result: ...

    def update(self, query: str) -> None: ...

    def serialize(
        self,
        destination: str | None = ...,
        format: str | None = ...,
        encoding: str | None = ...,
    ) -> str | bytes: ...

    def parse(
        self,
        source: str | None = ...,
        data: str | bytes | None = ...,
        format: str | None = ...,
    ) -> Graph: ...

    def bind(self, prefix: str, namespace: str) -> None: ...


__all__ = [
    "BNode",
    "Graph",
    "Literal",
    "OWL",
    "RDF",
    "RDFS",
    "URIRef",
    "exceptions",
    "plugin",
    "query",
    "term",
]
