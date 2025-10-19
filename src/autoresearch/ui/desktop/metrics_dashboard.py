"""Live metrics dashboard for the desktop interface."""

from __future__ import annotations

from typing import Any, Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget


class MetricsDashboard(QWidget):
    """Display runtime metrics in a tree-based dashboard."""

    def __init__(self) -> None:
        super().__init__()
        self._metrics: Mapping[str, Any] | None = None

        self._title = QLabel("Runtime Metrics")
        self._title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._title.setObjectName("metrics-dashboard-title")

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Metric", "Value"])
        self._tree.setRootIsDecorated(True)
        self._tree.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._tree)

    def update_metrics(self, metrics: Mapping[str, Any] | None) -> None:
        """Update the tree with the provided metrics mapping."""

        self._metrics = metrics or {}
        self._tree.clear()

        for key, value in sorted(self._metrics.items()):
            self._add_metric_item(self._tree.invisibleRootItem(), key, value)

        self._tree.expandAll()

    def clear(self) -> None:
        """Clear the tree and reset stored metrics."""

        self._metrics = None
        self._tree.clear()

    def _add_metric_item(self, parent: QTreeWidgetItem, key: str, value: Any) -> None:
        if isinstance(value, Mapping):
            item = QTreeWidgetItem([key, ""])  # Container node
            parent.addChild(item)
            for sub_key, sub_value in sorted(value.items()):
                self._add_metric_item(item, sub_key, sub_value)
            return

        item = QTreeWidgetItem([key, str(value)])
        parent.addChild(item)
