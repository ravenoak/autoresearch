"""Export management dock widget for the desktop UI."""

from __future__ import annotations

from typing import Mapping

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget


class ExportManager(QWidget):
    """Provide quick access to export actions exposed by the backend."""

    export_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._exports: dict[str, bool] = {}
        self._buttons: dict[str, QPushButton] = {}
        self._gating_enabled = False

        self._title = QLabel("Available Exports")
        self._title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.addStretch(1)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._container)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._scroll)

    def set_available_exports(self, exports: Mapping[str, bool] | None) -> None:
        """Render export buttons for the provided mapping."""

        self._exports = dict(exports or {})
        self._clear_buttons()
        self._buttons = {}

        for export_id, is_available in sorted(self._exports.items()):
            label = export_id.replace("_", " ").title()
            button = QPushButton(f"Export {label}")
            button.setEnabled(is_available and not self._gating_enabled)
            button.clicked.connect(lambda _=False, value=export_id: self.export_requested.emit(value))
            self._container_layout.insertWidget(self._container_layout.count() - 1, button)
            self._buttons[export_id] = button

        if not self._exports:
            placeholder = QLabel("No exports available for the current session.")
            placeholder.setAlignment(Qt.AlignCenter)
            self._container_layout.insertWidget(self._container_layout.count() - 1, placeholder)

    def set_export_gating(self, gated: bool) -> None:
        """Enable or disable export buttons without discarding them."""

        self._gating_enabled = gated

        for export_id, button in self._buttons.items():
            is_available = self._exports.get(export_id, False)
            button.setEnabled(is_available and not self._gating_enabled)

    def _clear_buttons(self) -> None:
        while self._container_layout.count() > 1:
            item = self._container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
