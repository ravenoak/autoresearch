"""Knowledge graph visualization widget for the desktop interface."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAction,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QLabel,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

try:  # pragma: no cover - optional dependency
    import networkx as nx  # type: ignore
except Exception:  # pragma: no cover - executed when networkx is unavailable
    nx = None  # type: ignore


class KnowledgeGraphView(QWidget):
    """Render knowledge graph data within a Qt widget."""

    def __init__(self) -> None:
        super().__init__()
        self._graph_data: Mapping[str, Any] | None = None
        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHints(
            self._view.renderHints() | QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        self._message = QLabel("Knowledge graph data will appear here when available.")
        self._message.setAlignment(Qt.AlignCenter)

        self._toolbar = QToolBar(self)
        self._toolbar.setIconSize(self._toolbar.iconSize())
        self._add_toolbar_actions()

        layout = QVBoxLayout(self)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._view)
        layout.addWidget(self._message)

        self._update_message_visibility()

    def _add_toolbar_actions(self) -> None:
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(lambda: self._scale_view(1.2))
        self._toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(lambda: self._scale_view(1 / 1.2))
        self._toolbar.addAction(zoom_out_action)

        reset_action = QAction("Reset", self)
        reset_action.triggered.connect(self._reset_view)
        self._toolbar.addAction(reset_action)

    def _scale_view(self, factor: float) -> None:
        self._view.scale(factor, factor)

    def _reset_view(self) -> None:
        self._view.resetTransform()
        self._view.ensureVisible(self._scene.itemsBoundingRect())

    def set_graph_data(self, graph_data: Mapping[str, Any] | Any | None) -> None:
        """Populate the widget with knowledge graph data."""

        self._graph_data = self._normalise_graph_data(graph_data)
        self._render_graph()

    def clear(self) -> None:
        """Clear the rendered graph and show the empty message."""

        self._graph_data = None
        self._scene.clear()
        self._update_message_visibility()

    def _normalise_graph_data(self, graph_data: Mapping[str, Any] | Any | None) -> Mapping[str, Any] | None:
        if graph_data is None:
            return None

        if nx and isinstance(graph_data, nx.Graph):  # pragma: no branch - depends on optional import
            return {
                "nodes": list(graph_data.nodes()),
                "edges": [tuple(edge) for edge in graph_data.edges()],
            }

        if isinstance(graph_data, Mapping):
            nodes = graph_data.get("nodes")
            edges = graph_data.get("edges")
            if nodes is not None and edges is not None:
                return {"nodes": list(nodes), "edges": list(edges)}

        return None

    def _render_graph(self) -> None:
        self._scene.clear()

        if not self._graph_data:
            self._update_message_visibility()
            return

        nodes: Sequence[Any] = self._graph_data.get("nodes", [])  # type: ignore[assignment]
        edges: Sequence[Sequence[Any]] = self._graph_data.get("edges", [])  # type: ignore[assignment]

        if not nodes:
            self._update_message_visibility()
            return

        self._message.hide()

        radius = 200
        count = len(nodes)
        for index, node in enumerate(nodes):
            angle = (2 * math.pi * index) / max(count, 1)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            position = QPointF(x, y)
            ellipse = self._scene.addEllipse(
                position.x() - 20, position.y() - 20, 40, 40, QPen(Qt.black), QColor("#e8f4ff")
            )
            ellipse.setToolTip(str(node))
            label = QGraphicsTextItem(str(node))
            label.setPos(position.x() - label.boundingRect().width() / 2, position.y() - 10)
            self._scene.addItem(label)

        pen = QPen(Qt.gray)
        pen.setWidth(2)
        for edge in edges:
            if len(edge) < 2:
                continue
            try:
                source_index = nodes.index(edge[0])
                target_index = nodes.index(edge[1])
            except ValueError:
                continue

            source_angle = (2 * math.pi * source_index) / max(count, 1)
            target_angle = (2 * math.pi * target_index) / max(count, 1)
            source_point = QPointF(radius * math.cos(source_angle), radius * math.sin(source_angle))
            target_point = QPointF(radius * math.cos(target_angle), radius * math.sin(target_angle))
            line = QGraphicsLineItem(source_point.x(), source_point.y(), target_point.x(), target_point.y())
            line.setPen(pen)
            self._scene.addItem(line)

        self._reset_view()

    def _update_message_visibility(self) -> None:
        if self._graph_data:
            self._message.hide()
        else:
            self._message.show()
            self._view.setSceneRect(-150, -150, 300, 300)
