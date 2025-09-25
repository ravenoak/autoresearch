"""Typed stub for the :mod:`networkx` package."""

from __future__ import annotations

from types import ModuleType
from typing import Any, Protocol, cast

from ._registry import install_stub_module


class Graph:
    """Minimal graph stub that accepts arbitrary constructor arguments."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - trivial
        return None


class DiGraph(Graph):
    """Minimal directed graph stub."""


class NetworkXModule(Protocol):
    Graph: type[Graph]
    DiGraph: type[DiGraph]


class _NetworkXModule(ModuleType):
    Graph = Graph
    DiGraph = DiGraph

    def __init__(self) -> None:
        super().__init__("networkx")


networkx = cast(NetworkXModule, install_stub_module("networkx", _NetworkXModule))

__all__ = ["DiGraph", "Graph", "NetworkXModule", "networkx"]
