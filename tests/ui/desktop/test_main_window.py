"""Unit tests for the desktop main window cancellation lifecycle."""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import Any

import pytest

QtCore = pytest.importorskip(
    "PySide6.QtCore",
    reason="PySide6 is required for desktop UI tests",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for desktop UI tests",
    exc_type=ImportError,
)

Qt = QtCore.Qt

from PySide6.QtWidgets import QMessageBox

from autoresearch.ui.desktop.main_window import AutoresearchMainWindow

pytestmark = pytest.mark.requires_ui


class _BlockingOrchestrator:
    """Stub orchestrator that waits for tests to unblock the worker."""

    def __init__(self) -> None:
        self._release = threading.Event()
        self.queries: list[str] = []

    def run_query(self, query: str, _config: Any) -> Any:
        self.queries.append(query)
        if not self._release.wait(timeout=5):
            raise TimeoutError("test orchestrator was not released")
        return SimpleNamespace(
            query=query,
            answer="cancel flow should drop this answer",
            citations=[],
            reasoning=[],
            metrics={},
        )

    def allow_completion(self) -> None:
        """Release the orchestrator so the worker run loop finishes."""

        self._release.set()


def _install_noop_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace ``load_configuration`` with a no-op for isolated tests."""

    monkeypatch.setattr(
        AutoresearchMainWindow,
        "load_configuration",
        lambda self: None,
    )


def test_cancel_query_lifecycle_restores_controls(
    qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cancelling a running query confirms, disables controls, and recovers cleanly."""

    _install_noop_loader(monkeypatch)

    window = AutoresearchMainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    orchestrator = _BlockingOrchestrator()
    window.orchestrator = orchestrator
    window.config = SimpleNamespace(reasoning_mode="balanced", loops=2)

    captured_dialog: dict[str, str] = {}

    def _fake_question(title: str, message: str, *_args: Any) -> int:
        captured_dialog["title"] = title
        captured_dialog["message"] = message
        return QMessageBox.Yes

    monkeypatch.setattr(window, "_ask_question", _fake_question)

    emitted_events: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(
        "autoresearch.ui.desktop.main_window.telemetry.emit",
        lambda name, payload: emitted_events.append((name, payload)),
    )

    panel = window.query_panel
    assert panel is not None
    assert panel.run_button is not None
    assert panel.cancel_button is not None

    panel.set_query_text("cancelled query scenario")
    qtbot.mouseClick(panel.run_button, Qt.LeftButton)

    qtbot.waitUntil(lambda: window.is_query_running, timeout=1000)
    assert panel.cancel_button.isVisible()
    assert panel.cancel_button.isEnabled()

    qtbot.mouseClick(panel.cancel_button, Qt.LeftButton)

    qtbot.waitUntil(lambda: window._status_message == "Cancelling…", timeout=1000)
    assert not panel.cancel_button.isEnabled()
    assert captured_dialog == {
        "title": "Cancel query?",
        "message": "Cancel the active query? This action cannot be undone.",
    }

    orchestrator.allow_completion()

    qtbot.waitUntil(lambda: not window.is_query_running, timeout=2000)
    qtbot.waitUntil(lambda: not panel.is_busy(), timeout=2000)
    qtbot.waitUntil(lambda: not window.progress_bar.isVisible(), timeout=2000)
    qtbot.waitUntil(lambda: window._worker_thread is None, timeout=2000)

    assert window._status_message == "Ready"
    assert window._latest_metrics_payload is None
    assert not panel.cancel_button.isVisible()
    assert window._cancelled_session_ids == set()
    assert window._active_worker is None

    assert emitted_events
    event_name, payload = emitted_events[-1]
    assert event_name == "ui.query.cancelled"
    assert payload.get("status") == "cancelled"

    assert orchestrator.queries == ["cancelled query scenario"]
