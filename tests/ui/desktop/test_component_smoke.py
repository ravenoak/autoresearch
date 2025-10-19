"""Smoke tests for PySide6 desktop widgets."""

from __future__ import annotations

import pytest

QtCore = pytest.importorskip(
    "PySide6.QtCore",
    reason="PySide6 is required for desktop UI smoke tests",
    exc_type=ImportError,
)
QtWidgets = pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for desktop UI smoke tests",
    exc_type=ImportError,
)

Qt = QtCore.Qt
QListWidget = QtWidgets.QListWidget
QPushButton = QtWidgets.QPushButton

from autoresearch.ui.desktop import (
    AutoresearchMainWindow,
    ConfigEditor,
    ExportManager,
    KnowledgeGraphView,
    MetricsDashboard,
    SessionManager,
)

pytestmark = pytest.mark.requires_ui


def test_knowledge_graph_view_smoke(qtbot) -> None:
    view = KnowledgeGraphView()
    qtbot.addWidget(view)

    view.set_graph_data({"nodes": ["A", "B", "C"], "edges": [["A", "B"], ["B", "C"]]})
    view.set_graph_data(None)


def test_metrics_dashboard_smoke(qtbot) -> None:
    dashboard = MetricsDashboard()
    qtbot.addWidget(dashboard)

    dashboard.update_metrics({"tokens": {"prompt": 42, "completion": 64}})
    dashboard.clear()


def test_config_editor_smoke(qtbot) -> None:
    editor = ConfigEditor()
    qtbot.addWidget(editor)

    editor.load_config({"profile": "test", "limits": {"loops": 3}})
    apply_button = next(
        button for button in editor.findChildren(QPushButton) if button.text().startswith("Apply")
    )
    qtbot.mouseClick(apply_button, Qt.LeftButton)


def test_session_manager_smoke(qtbot) -> None:
    manager = SessionManager()
    qtbot.addWidget(manager)

    manager.add_session("session-1", "Exploratory Query")
    list_widget = manager.findChild(QListWidget)
    assert list_widget is not None
    assert "Exploratory" in list_widget.item(0).text()


def test_export_manager_smoke(qtbot) -> None:
    manager = ExportManager()
    qtbot.addWidget(manager)

    manager.set_available_exports({"graphml": True, "graph_json": False})
    buttons = [button for button in manager.findChildren(QPushButton) if button.isEnabled()]
    assert buttons
    qtbot.mouseClick(buttons[0], Qt.LeftButton)


def test_main_window_smoke(qtbot) -> None:
    window = AutoresearchMainWindow()
    qtbot.addWidget(window)

    assert window.config_editor is not None
    assert window.session_manager is not None
    assert window.export_manager is not None
