"""Session management dock widget for the desktop UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass
class SessionEntry:
    """Simple data carrier for session metadata."""

    session_id: str
    title: str
    created_at: datetime


@dataclass
class WorkspaceEntry:
    """Metadata describing a workspace manifest selection."""

    workspace_id: str
    title: str
    version: int
    manifest_id: str | None = None


class SessionManager(QWidget):
    """Display known sessions and emit signals for selection or creation."""

    session_selected = Signal(str)
    new_session_requested = Signal()
    workspace_selected = Signal(str, object, int)
    new_workspace_requested = Signal()
    workspace_debate_requested = Signal(str, object, int)

    def __init__(self) -> None:
        super().__init__()
        self._sessions: dict[str, SessionEntry] = {}
        self._workspaces: dict[str, WorkspaceEntry] = {}

        self._list = QListWidget()
        self._list.itemActivated.connect(self._emit_selection)

        self._workspace_list = QListWidget()
        self._workspace_list.itemActivated.connect(self._emit_workspace_selection)

        self._new_session_button = QPushButton("New Session")
        self._new_session_button.clicked.connect(self._request_new_session)

        self._new_workspace_button = QPushButton("New Workspace")
        self._new_workspace_button.clicked.connect(self._request_new_workspace)

        self._start_debate_button = QPushButton("Start Debate")
        self._start_debate_button.clicked.connect(self._request_workspace_debate)

        layout = QVBoxLayout(self)

        session_label = QLabel("Sessions")
        session_label.setObjectName("session-manager-sessions-label")
        layout.addWidget(session_label)
        layout.addWidget(self._list)

        session_buttons = QHBoxLayout()
        session_buttons.addWidget(self._new_session_button)
        session_buttons.addStretch(1)
        layout.addLayout(session_buttons)

        workspace_label = QLabel("Workspaces")
        workspace_label.setObjectName("session-manager-workspaces-label")
        layout.addWidget(workspace_label)
        layout.addWidget(self._workspace_list)

        workspace_buttons = QHBoxLayout()
        workspace_buttons.addWidget(self._new_workspace_button)
        workspace_buttons.addWidget(self._start_debate_button)
        workspace_buttons.addStretch(1)
        layout.addLayout(workspace_buttons)

    def add_session(self, session_id: str, title: str) -> None:
        """Add a session to the list and persist metadata."""

        entry = SessionEntry(session_id=session_id, title=title, created_at=datetime.now())
        self._sessions[session_id] = entry

        item = QListWidgetItem(f"{title} ({entry.created_at.strftime('%H:%M:%S')})")
        item.setData(Qt.UserRole, session_id)  # type: ignore[attr-defined]
        self._list.addItem(item)

    def _emit_selection(self, item: QListWidgetItem) -> None:
        session_id = item.data(Qt.UserRole)  # type: ignore[attr-defined]
        if session_id:
            self.session_selected.emit(str(session_id))

    def _request_new_session(self) -> None:
        self.new_session_requested.emit()

    def add_workspace(
        self,
        workspace_id: str,
        title: str,
        version: int,
        manifest_id: str | None = None,
    ) -> None:
        """Register a workspace manifest entry in the UI."""

        entry = WorkspaceEntry(
            workspace_id=workspace_id,
            title=title,
            version=version,
            manifest_id=manifest_id,
        )
        self._workspaces[workspace_id] = entry

        display = f"{title} (v{version})"
        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, workspace_id)  # type: ignore[attr-defined]
        item.setData(Qt.UserRole + 1, manifest_id)  # type: ignore[attr-defined]
        self._workspace_list.addItem(item)

    def clear_workspaces(self) -> None:
        """Remove all workspace entries from the list."""

        self._workspaces.clear()
        self._workspace_list.clear()

    def _emit_workspace_selection(self, item: QListWidgetItem) -> None:
        workspace_id = item.data(Qt.UserRole)  # type: ignore[attr-defined]
        manifest_id = item.data(Qt.UserRole + 1)  # type: ignore[attr-defined]
        if workspace_id:
            entry = self._workspaces.get(str(workspace_id))
            version = entry.version if entry else 0
            self.workspace_selected.emit(str(workspace_id), manifest_id, version)

    def _request_new_workspace(self) -> None:
        self.new_workspace_requested.emit()

    def _request_workspace_debate(self) -> None:
        current_item = self._workspace_list.currentItem()
        if current_item is None:
            return
        workspace_id = current_item.data(Qt.UserRole)  # type: ignore[attr-defined]
        manifest_id = current_item.data(Qt.UserRole + 1)  # type: ignore[attr-defined]
        if workspace_id:
            entry = self._workspaces.get(str(workspace_id))
            version = entry.version if entry else 0
            self.workspace_debate_requested.emit(str(workspace_id), manifest_id, version)
