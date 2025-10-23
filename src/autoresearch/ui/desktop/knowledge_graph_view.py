"""Knowledge graph visualization widget for the desktop interface."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QImage, QPainter, QPen
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
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
        self._layout_mode = "circular"
        self._selected_element: tuple[Any, ...] | None = None
        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHints(
            self._view.renderHints() | QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        self._scene.selectionChanged.connect(self._handle_selection_change)
        self._message = QLabel("Knowledge graph data will appear here when available.")
        self._message.setAlignment(Qt.AlignCenter)

        self._toolbar = QToolBar(self)
        self._toolbar.setIconSize(self._toolbar.iconSize())
        self._node_items: list[QGraphicsEllipseItem] = []
        self._edge_items: list[QGraphicsLineItem] = []
        self._export_actions: list[QAction] = []
        self._layout_actions: dict[str, QAction] = {}
        self._add_toolbar_actions()

        self._details_label = QLabel("Select a node or edge to view details.")
        self._details_label.setWordWrap(True)
        self._details_label.setMinimumWidth(220)

        graph_container = QWidget(self)
        graph_layout = QHBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(12)
        graph_layout.addWidget(self._view, stretch=1)
        graph_layout.addWidget(self._details_label)

        layout = QVBoxLayout(self)
        layout.addWidget(self._toolbar)
        layout.addWidget(graph_container)
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

        self._toolbar.addSeparator()

        layout_group = QActionGroup(self)
        layout_group.setExclusive(True)

        for layout_key, label in (
            ("circular", "Circular Layout"),
            ("spring", "Spring Layout"),
            ("spectral", "Spectral Layout"),
        ):
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(layout_key == self._layout_mode)
            action.triggered.connect(lambda checked, key=layout_key: self._set_layout_mode(key))
            layout_group.addAction(action)
            if layout_key != "circular" and nx is None:  # pragma: no cover - optional dependency
                action.setEnabled(False)
            self._layout_actions[layout_key] = action
            self._toolbar.addAction(action)

        self._toolbar.addSeparator()

        export_png_action = QAction("Export PNG", self)
        export_png_action.triggered.connect(lambda: self._prompt_export("png"))
        self._toolbar.addAction(export_png_action)

        export_pdf_action = QAction("Export PDF", self)
        export_pdf_action.triggered.connect(lambda: self._prompt_export("pdf"))
        self._toolbar.addAction(export_pdf_action)

        export_svg_action = QAction("Export SVG", self)
        export_svg_action.triggered.connect(lambda: self._prompt_export("svg"))
        self._toolbar.addAction(export_svg_action)

        self._export_actions = [export_png_action, export_pdf_action, export_svg_action]
        self._update_export_actions_state()

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
        self._node_items.clear()
        self._edge_items.clear()
        self._selected_element = None
        self._update_message_visibility()
        self._details_label.setText("Select a node or edge to view details.")
        self._update_export_actions_state()

    @property
    def selected_element(self) -> tuple[Any, ...] | None:
        """Return the currently selected element, if any."""

        return self._selected_element

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
        previously_selected = self._selected_element
        self._scene.clear()
        self._node_items.clear()
        self._edge_items.clear()
        self._selected_element = None

        if not self._graph_data:
            self._update_message_visibility()
            return

        nodes: Sequence[Any] = self._graph_data.get("nodes", [])  # type: ignore[assignment]
        edges: Sequence[Sequence[Any]] = self._graph_data.get("edges", [])  # type: ignore[assignment]

        if not nodes:
            self._update_message_visibility()
            return

        self._message.hide()

        positions = self._compute_layout_positions(nodes, edges)

        for node in nodes:
            position = positions.get(node)
            if position is None:
                continue

            ellipse = self._scene.addEllipse(
                position.x() - 20,
                position.y() - 20,
                40,
                40,
                QPen(Qt.black),
                QColor("#e8f4ff"),
            )
            ellipse.setBrush(QColor("#e8f4ff"))
            ellipse.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            ellipse.setData(0, ("node", node))
            ellipse.setZValue(1)
            ellipse.setToolTip(str(node))
            self._node_items.append(ellipse)

            label = QGraphicsTextItem(str(node))
            label_width = label.boundingRect().width()
            label.setPos(position.x() - (label_width / 2), position.y() - 10)
            self._scene.addItem(label)

        pen = QPen(Qt.gray)
        pen.setWidth(2)
        for edge in edges:
            if len(edge) < 2:
                continue
            source = edge[0]
            target = edge[1]
            source_point = positions.get(source)
            target_point = positions.get(target)
            if source_point is None or target_point is None:
                continue

            line = QGraphicsLineItem(
                source_point.x(),
                source_point.y(),
                target_point.x(),
                target_point.y(),
            )
            line.setPen(pen)
            line.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            line.setData(0, ("edge", source, target))
            line.setToolTip(f"{source} → {target}")
            line.setZValue(0)
            self._scene.addItem(line)
            self._edge_items.append(line)

        self._reset_view()
        self._update_export_actions_state()

        if previously_selected is not None:
            self._restore_selection(previously_selected)

    def _update_message_visibility(self) -> None:
        if self._graph_data:
            self._message.hide()
        else:
            self._message.show()
            self._view.setSceneRect(-150, -150, 300, 300)
            self._details_label.setText("Select a node or edge to view details.")

    def _compute_layout_positions(
        self, nodes: Sequence[Any], edges: Sequence[Sequence[Any]]
    ) -> dict[Any, QPointF]:
        if self._layout_mode == "circular" or nx is None:
            return self._circular_layout(nodes)

        try:
            graph = nx.Graph()
            graph.add_nodes_from(nodes)
            processed_edges = [tuple(edge[:2]) for edge in edges if len(edge) >= 2]
            graph.add_edges_from(processed_edges)

            if self._layout_mode == "spring":
                positions = nx.spring_layout(graph, seed=42)  # type: ignore[call-arg]
            elif self._layout_mode == "spectral":
                positions = nx.spectral_layout(graph)  # type: ignore[assignment]
            else:
                return self._circular_layout(nodes)
        except Exception:  # pragma: no cover - networkx failure path
            return self._circular_layout(nodes)

        if not positions:
            return self._circular_layout(nodes)

        max_abs = max((abs(coord) for pos in positions.values() for coord in pos), default=1.0)
        scale = 200 / max_abs if max_abs else 200

        return {
            node: QPointF(float(pos[0]) * scale, float(pos[1]) * scale)
            for node, pos in positions.items()
        }

    def _circular_layout(self, nodes: Sequence[Any]) -> dict[Any, QPointF]:
        radius = 200
        count = max(len(nodes), 1)
        positions: dict[Any, QPointF] = {}
        for index, node in enumerate(nodes):
            angle = (2 * math.pi * index) / count
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            positions[node] = QPointF(x, y)
        return positions

    def _handle_selection_change(self) -> None:
        selected_items = self._scene.selectedItems()
        if not selected_items:
            self._selected_element = None
            self._details_label.setText("Select a node or edge to view details.")
            self._update_item_styles()
            return

        item = selected_items[0]
        element_data = item.data(0)
        if isinstance(element_data, tuple):
            self._selected_element = tuple(element_data)
        else:
            self._selected_element = None

        self._details_label.setText(self._format_element_details(self._selected_element))
        self._update_item_styles()

    def _update_item_styles(self) -> None:
        for node_item in self._node_items:
            is_selected = node_item.isSelected()
            node_item.setBrush(QColor("#bee3f8") if is_selected else QColor("#e8f4ff"))
            pen = QPen(Qt.black)
            pen.setWidth(3 if is_selected else 1)
            node_item.setPen(pen)

        for edge_item in self._edge_items:
            pen = QPen(QColor("#2b6cb0") if edge_item.isSelected() else Qt.gray)
            pen.setWidth(3 if edge_item.isSelected() else 2)
            edge_item.setPen(pen)

    def _format_element_details(self, element: tuple[Any, ...] | None) -> str:
        if element is None:
            return "Select a node or edge to view details."

        if not element:
            return "Select a node or edge to view details."

        element_type = element[0]
        if element_type == "node" and len(element) == 2:
            return f"Node: {element[1]}"

        if element_type == "edge" and len(element) >= 3:
            return f"Edge: {element[1]} → {element[2]}"

        return "Select a node or edge to view details."

    def _restore_selection(self, element: tuple[Any, ...]) -> None:
        for item in self._scene.items():
            if item.data(0) == element:
                item.setSelected(True)
                break

    def _prompt_export(self, file_type: str) -> None:
        if not self._graph_data:
            return

        filters = {
            "png": "PNG Files (*.png)",
            "pdf": "PDF Files (*.pdf)",
            "svg": "SVG Files (*.svg)",
        }
        default_suffix = file_type
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Graph as {file_type.upper()}",
            "",
            filters[file_type],
        )
        if not file_path:
            return

        if not file_path.lower().endswith(f".{default_suffix}"):
            file_path = f"{file_path}.{default_suffix}"

        if file_type == "png":
            self._export_png(file_path)
        elif file_type == "pdf":
            self._export_pdf(file_path)
        elif file_type == "svg":
            self._export_svg(file_path)

    def _export_png(self, file_path: str) -> None:
        rect = self._scene.itemsBoundingRect()
        if rect.isNull():
            return

        expanded = rect.adjusted(-20, -20, 20, 20)
        size = expanded.size().toSize()
        image = QImage(size, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        self._scene.render(painter, QRectF(0, 0, expanded.width(), expanded.height()), expanded)
        painter.end()
        image.save(file_path)

    def _export_pdf(self, file_path: str) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)

        painter = QPainter(printer)
        painter.setRenderHint(QPainter.Antialiasing)
        self._scene.render(painter)
        painter.end()

    def _export_svg(self, file_path: str) -> None:
        rect = self._scene.itemsBoundingRect()
        if rect.isNull():
            return

        expanded = rect.adjusted(-20, -20, 20, 20)
        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setViewBox(expanded)
        generator.setSize(expanded.size().toSize())

        painter = QPainter(generator)
        painter.setRenderHint(QPainter.Antialiasing)
        self._scene.render(painter, QRectF(0, 0, expanded.width(), expanded.height()), expanded)
        painter.end()

    def _update_export_actions_state(self) -> None:
        has_graph = bool(self._graph_data)
        for action in self._export_actions:
            action.setEnabled(has_graph)

    def _set_layout_mode(self, layout: str) -> None:
        if layout == self._layout_mode:
            return

        self._layout_mode = layout
        self._render_graph()
