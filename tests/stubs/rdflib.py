"""Typed stub for the :mod:`rdflib` package."""

from __future__ import annotations

from types import ModuleType
from typing import Any, Protocol, cast

from ._registry import install_stub_module


class Graph:
    """Minimal RDF graph stub."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - trivial
        return None

    def open(self, *args: Any, **kwargs: Any) -> Graph:
        return self


class RDFLibModule(Protocol):
    Graph: type[Graph]


class _RDFLibModule(ModuleType):
    Graph = Graph

    def __init__(self) -> None:
        super().__init__("rdflib")


rdflib = cast(RDFLibModule, install_stub_module("rdflib", _RDFLibModule))

__all__ = ["Graph", "RDFLibModule", "rdflib"]
