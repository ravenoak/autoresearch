"""Configuration editor dock widget for the desktop UI."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

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

    def apply_repository_manifest(
        self, manifest: Sequence[Mapping[str, Any]]
    ) -> None:
        """Replace the repository manifest section within the editor."""

        manifest_payload = [dict(entry) for entry in manifest]
        content = self._editor.toPlainText().strip()
        try:
            parsed = json.loads(content) if content else {}
        except json.JSONDecodeError:
            parsed = {}
        if not isinstance(parsed, dict):
            parsed = {}
        search_cfg = parsed.setdefault("search", {})
        if not isinstance(search_cfg, dict):
            search_cfg = {}
            parsed["search"] = search_cfg
        local_git = search_cfg.setdefault("local_git", {})
        if not isinstance(local_git, dict):
            local_git = {}
            search_cfg["local_git"] = local_git
        local_git["manifest"] = manifest_payload
        serialised = json.dumps(parsed, indent=2, sort_keys=True)
        self._editor.setPlainText(serialised)

    def extract_repository_manifest(self) -> list[dict[str, Any]]:
        """Return the manifest currently encoded in the editor content."""

        text = self._editor.toPlainText().strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, dict):
            return []
        search_cfg = parsed.get("search", {})
        if not isinstance(search_cfg, Mapping):
            return []
        local_git = search_cfg.get("local_git", {})
        if not isinstance(local_git, Mapping):
            return []
        manifest = local_git.get("manifest", [])
        results: list[dict[str, Any]] = []
        if isinstance(manifest, list):
            for entry in manifest:
                if isinstance(entry, Mapping):
                    results.append(dict(entry))
        return results

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
