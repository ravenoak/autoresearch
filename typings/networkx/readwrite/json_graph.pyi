from __future__ import annotations

from typing import Any

from .. import DiGraph, MultiDiGraph


def node_link_data(graph: DiGraph[Any] | MultiDiGraph[Any]) -> dict[str, Any]: ...


__all__ = ["node_link_data"]
