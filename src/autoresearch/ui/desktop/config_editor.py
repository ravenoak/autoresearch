"""Configuration editor dock widget for the desktop UI."""

from __future__ import annotations

import json
from typing import Any, Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ConfigEditor(QWidget):
    """Provide a lightweight configuration editor with JSON previews."""

    configuration_changed = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._editor = QTextEdit()
        self._editor.setPlaceholderText("Configuration will load after initialization.")
        self._editor.setAcceptRichText(False)
        self._original_content: str | None = None

        self._apply_button = QPushButton("Apply Changes")
        self._apply_button.clicked.connect(self._emit_configuration)

        self._reset_button = QPushButton("Reset")
        self._reset_button.clicked.connect(self._reset_content)

        button_row = QHBoxLayout()
        button_row.addWidget(self._apply_button)
        button_row.addWidget(self._reset_button)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._editor)
        layout.addLayout(button_row)

    def load_config(self, config: Any) -> None:
        """Load the provided configuration into the editor."""

        serialised = self._serialise_config(config)
        self._original_content = serialised
        self._editor.setPlainText(serialised)

    def _serialise_config(self, config: Any) -> str:
        if config is None:
            return "{}"

        if hasattr(config, "model_dump"):
            data = config.model_dump()
        elif hasattr(config, "dict"):
            data = config.dict()
        elif isinstance(config, Mapping):
            data = dict(config)
        else:
            data = getattr(config, "__dict__", {})

        try:
            return json.dumps(data, indent=2, sort_keys=True)
        except TypeError:
            return json.dumps({}, indent=2)

    def _emit_configuration(self) -> None:
        text = self._editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Configuration", "Configuration content cannot be empty.")
            return

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:  # pragma: no cover - UI feedback path
            QMessageBox.warning(self, "Configuration", f"Invalid JSON: {exc}")
            return

        if not isinstance(parsed, dict):
            QMessageBox.warning(
                self,
                "Configuration",
                "Configuration must decode to a JSON object.",
            )
            return

        self.configuration_changed.emit(parsed)

    def _reset_content(self) -> None:
        if self._original_content is None:
            return
        self._editor.setPlainText(self._original_content)
