"""Session management dock widget for the desktop UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
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


class SessionManager(QWidget):
    """Display known sessions and emit signals for selection or creation."""

    session_selected = Signal(str)
    new_session_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._sessions: dict[str, SessionEntry] = {}

        self._list = QListWidget()
        self._list.itemActivated.connect(self._emit_selection)

        self._new_button = QPushButton("New Session")
        self._new_button.clicked.connect(self._request_new_session)

        button_row = QHBoxLayout()
        button_row.addWidget(self._new_button)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        layout.addLayout(button_row)

    def add_session(self, session_id: str, title: str) -> None:
        """Add a session to the list and persist metadata."""

        entry = SessionEntry(session_id=session_id, title=title, created_at=datetime.now())
        self._sessions[session_id] = entry

        item = QListWidgetItem(f"{title} ({entry.created_at.strftime('%H:%M:%S')})")
        item.setData(Qt.UserRole, session_id)
        self._list.addItem(item)

    def _emit_selection(self, item: QListWidgetItem) -> None:
        session_id = item.data(Qt.UserRole)
        if session_id:
            self.session_selected.emit(str(session_id))

    def _request_new_session(self) -> None:
        self.new_session_requested.emit()
