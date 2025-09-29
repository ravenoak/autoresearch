from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator, Mapping, MutableMapping, Sequence
from typing import Any, Generic, TypeVar

NodeT = TypeVar("NodeT", bound=Hashable)
_NodeT = TypeVar("_NodeT")

NodeData = MutableMapping[str, Any]


class NodeView(Mapping[_NodeT, NodeData], Generic[_NodeT]):
    def __call__(self, data: bool = ..., default: Any = ...) -> Iterable[_NodeT] | Iterable[tuple[_NodeT, NodeData]]: ...

    def __iter__(self) -> Iterator[_NodeT]: ...

    def __len__(self) -> int: ...

    def __contains__(self, node: object) -> bool: ...

    def __getitem__(self, node: _NodeT) -> NodeData: ...


class DiGraph(Generic[_NodeT]):
    def __init__(self, incoming_graph_data: Any | None = ..., **attr: Any) -> None: ...

    nodes: NodeView[_NodeT]

    def add_node(self, node_for_adding: _NodeT, **attr: Any) -> None: ...

    def add_edge(self, u_of_edge: _NodeT, v_of_edge: _NodeT, **attr: Any) -> None: ...

    def remove_node(self, n: _NodeT) -> None: ...

    def remove_edge(self, u: _NodeT, v: _NodeT) -> None: ...

    def edges(
        self, data: bool = ..., default: Any = ...
    ) -> Iterable[tuple[_NodeT, _NodeT]] | Iterable[tuple[_NodeT, _NodeT, dict[str, Any]]]: ...

    def has_node(self, n: _NodeT) -> bool: ...

    def number_of_nodes(self) -> int: ...

    def degree(self) -> Mapping[_NodeT, int]: ...

    def clear(self) -> None: ...

    def __iter__(self) -> Iterator[_NodeT]: ...


class MultiDiGraph(Generic[_NodeT]):
    def __init__(self, incoming_graph_data: Any | None = ..., **attr: Any) -> None: ...

    nodes: NodeView[_NodeT]

    def add_node(self, node_for_adding: _NodeT, **attr: Any) -> None: ...

    def add_edge(self, u_of_edge: _NodeT, v_of_edge: _NodeT, key: Any | None = ..., **attr: Any) -> None: ...

    def remove_node(self, n: _NodeT) -> None: ...

    def edges(
        self, data: bool = ..., default: Any = ...
    ) -> Iterable[tuple[_NodeT, _NodeT, Any]] | Iterable[tuple[_NodeT, _NodeT, Any, dict[str, Any]]]: ...

    def has_node(self, n: _NodeT) -> bool: ...

    def number_of_nodes(self) -> int: ...

    def clear(self) -> None: ...

    def __iter__(self) -> Iterator[_NodeT]: ...


def spring_layout(
    graph: DiGraph[NodeT] | MultiDiGraph[NodeT],
    *,
    seed: int | None = ...,
    center: tuple[float, float] | None = ...,
) -> dict[NodeT, tuple[float, float]]: ...


def circular_layout(
    graph: DiGraph[NodeT] | MultiDiGraph[NodeT],
) -> dict[NodeT, tuple[float, float]]: ...


def draw(graph: DiGraph[NodeT] | MultiDiGraph[NodeT], *args: Any, **kwargs: Any) -> None: ...


def draw_networkx_nodes(
    graph: DiGraph[NodeT] | MultiDiGraph[NodeT],
    pos: Mapping[NodeT, tuple[float, float]],
    *args: Any,
    **kwargs: Any,
) -> None: ...


def draw_networkx_edges(
    graph: DiGraph[NodeT] | MultiDiGraph[NodeT],
    pos: Mapping[NodeT, tuple[float, float]],
    *args: Any,
    **kwargs: Any,
) -> None: ...


def draw_networkx_labels(
    graph: DiGraph[NodeT] | MultiDiGraph[NodeT],
    pos: Mapping[NodeT, tuple[float, float]],
    *args: Any,
    **kwargs: Any,
) -> None: ...


def generate_graphml(graph: DiGraph[NodeT] | MultiDiGraph[NodeT]) -> Iterable[str]: ...


def all_simple_paths(
    graph: DiGraph[NodeT] | MultiDiGraph[NodeT],
    source: NodeT,
    target: NodeT,
    cutoff: int | None = ...,
) -> Iterable[list[NodeT]]: ...


__all__ = [
    "NodeView",
    "DiGraph",
    "MultiDiGraph",
    "spring_layout",
    "circular_layout",
    "draw",
    "draw_networkx_nodes",
    "draw_networkx_edges",
    "draw_networkx_labels",
    "generate_graphml",
    "all_simple_paths",
]
