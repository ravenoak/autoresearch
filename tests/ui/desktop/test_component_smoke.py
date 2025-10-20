"""Smoke tests for PySide6 desktop widgets."""

# Spec: docs/specs/pyside-desktop.md
from __future__ import annotations

from typing import Any, Mapping

import pytest

import autoresearch.ui.desktop.main_window as main_window_module

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
QLabel = QtWidgets.QLabel

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.ui.desktop import (
    AutoresearchMainWindow,
    ConfigEditor,
    ExportManager,
    KnowledgeGraphView,
    MetricsDashboard,
    SessionManager,
)
from autoresearch.ui.desktop.results_display import ResultsDisplay

pytestmark = pytest.mark.requires_ui


def test_knowledge_graph_view_smoke(qtbot) -> None:
    view = KnowledgeGraphView()
    qtbot.addWidget(view)

    view.set_graph_data({"nodes": ["A", "B", "C"], "edges": [["A", "B"], ["B", "C"]]})
    view.set_graph_data(None)


def test_metrics_dashboard_smoke(qtbot) -> None:
    dashboard = MetricsDashboard()
    qtbot.addWidget(dashboard)

    dashboard.update_metrics(
        {
            "system": {"cpu_percent": 37.5, "memory_percent": 62.0},
            "tokens": {"prompt": 42, "completion": 64},
        }
    )
    summary_label = dashboard.findChild(QLabel, "metrics-summary")
    assert summary_label is not None
    assert "Latest metrics snapshot" in summary_label.text()

    toggle_button = dashboard.findChild(QPushButton, "metrics-dashboard-toggle")
    assert toggle_button is not None
    if toggle_button.isEnabled():
        qtbot.mouseClick(toggle_button, Qt.LeftButton)
        assert toggle_button.isChecked()
    else:
        assert "Charts unavailable" in toggle_button.text()

    dashboard.clear()
    assert "Metrics not available" in summary_label.text()


def test_metrics_dashboard_auto_refresh(qtbot) -> None:
    dashboard = MetricsDashboard()
    qtbot.addWidget(dashboard)

    samples = [
        {"system": {"cpu_percent": 10.0, "memory_percent": 25.0}, "tokens": {"prompt": 10}},
        {
            "system": {"cpu_percent": 20.0, "memory_percent": 40.0},
            "tokens": {"prompt": 10, "completion": 15},
        },
    ]
    index = {"value": 0}

    def provider() -> Mapping[str, float | dict[str, float]] | None:
        if index["value"] >= len(samples):
            return None
        snapshot = samples[index["value"]]
        index["value"] += 1
        return snapshot

    dashboard.bind_metrics_provider(provider, interval_ms=50)
    qtbot.wait(200)
    dashboard.bind_metrics_provider(None)

    summary_label = dashboard.findChild(QLabel, "metrics-summary")
    assert summary_label is not None
    text = summary_label.text()
    assert "Latest metrics snapshot" in text
    assert "Auto-refresh enabled" not in text
    toggle_button = dashboard.findChild(QPushButton, "metrics-dashboard-toggle")
    assert toggle_button is not None
    if not toggle_button.isEnabled():
        assert "Charts unavailable" in text


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


def test_main_window_applies_query_panel_overrides(qtbot, monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class DummyLoader:
        def load_config(self) -> ConfigModel:
            return ConfigModel()

    class DummyOrchestrator:
        def run_query(self, query: str, config: ConfigModel) -> QueryResponse:
            captured["query"] = query
            captured["config"] = config
            return QueryResponse(
                query=query,
                answer="ok",
                citations=[],
                reasoning=[],
                metrics={},
                warnings=[],
                claim_audits=[],
                task_graph=None,
                react_traces=[],
                state_id=None,
            )

    monkeypatch.setattr(main_window_module, "ConfigLoader", DummyLoader)
    monkeypatch.setattr(main_window_module, "Orchestrator", DummyOrchestrator)

    class ImmediateThreadPool:
        def start(self, worker) -> None:
            worker.run()

    monkeypatch.setattr(
        QtCore.QThreadPool,
        "globalInstance",
        staticmethod(lambda: ImmediateThreadPool()),
    )

    def immediate_single_shot(_interval: int, receiver, slot=None) -> None:
        callback = slot or receiver
        callback()

    monkeypatch.setattr(QtCore.QTimer, "singleShot", staticmethod(immediate_single_shot))

    window = AutoresearchMainWindow()
    qtbot.addWidget(window)

    assert window.query_panel is not None
    combo = window.query_panel.reasoning_mode_combo
    assert combo is not None
    combo.setCurrentText(ReasoningMode.CHAIN_OF_THOUGHT.value)

    spinbox = window.query_panel.loops_spinbox
    assert spinbox is not None
    spinbox.setValue(5)

    window.on_query_submitted("Test query")
    qtbot.waitUntil(lambda: "config" in captured, timeout=500)

    config = captured["config"]
    assert getattr(config, "loops", None) == 5
    assert getattr(config, "reasoning_mode", None) == ReasoningMode.CHAIN_OF_THOUGHT

    assert window.config_editor is not None
    editor_text = window.config_editor._editor.toPlainText()
    assert '"loops": 5' in editor_text
    assert '"reasoning_mode": "chain-of-thought"' in editor_text


def test_results_display_citations_tab_and_controls(qtbot) -> None:
    display = ResultsDisplay()
    qtbot.addWidget(display)

    assert display.tab_widget is not None
    tab_titles = [display.tab_widget.tabText(i) for i in range(display.tab_widget.count())]
    assert "Citations" in tab_titles

    result = QueryResponse(
        query="Test",
        answer="Sample answer",
        citations=[
            "https://example.com/resource",
            {"title": "Spec", "url": "https://example.org/spec"},
        ],
        reasoning=[],
        metrics={},
        warnings=[],
        claim_audits=[],
        task_graph=None,
        react_traces=[],
        state_id=None,
    )

    display.display_results(result)

    assert display.citations_list is not None
    assert display.citations_list.count() == 2
    assert display.open_source_button is not None
    assert display.copy_source_button is not None
    assert display.open_source_button.isEnabled()
    assert display.copy_source_button.isEnabled()


def test_results_display_markdown_conversion_handles_rich_content(qtbot) -> None:
    display = ResultsDisplay()
    qtbot.addWidget(display)

    html = display.render_markdown(
        """# Heading

- Item one
- Item two

This is *important* information.

<script>alert('x');</script>
"""
    )

    assert "<h1>Heading</h1>" in html
    assert html.count("<li>") == 2
    assert "<em>important</em>" in html
    assert "<script>" not in html
