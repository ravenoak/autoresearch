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
QMessageBox = QtWidgets.QMessageBox

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
from autoresearch.ui.desktop.telemetry import (
    DESKTOP_TELEMETRY_CATEGORY,
    DesktopTelemetry,
    get_dispatcher,
    set_dispatcher,
)

pytestmark = pytest.mark.requires_ui


@pytest.fixture
def telemetry_events() -> list[tuple[str, Mapping[str, Any]]]:
    original_dispatcher = get_dispatcher()
    captured: list[tuple[str, Mapping[str, Any]]] = []

    def _collector(event: str, payload: Mapping[str, Any]) -> None:
        captured.append((event, payload))

    set_dispatcher(_collector)

    yield captured

    set_dispatcher(original_dispatcher)


def test_desktop_telemetry_emits_default_category(monkeypatch) -> None:
    emitted: dict[str, Any] = {}

    def fake_qcinfo(category: Any, message: str) -> None:
        emitted["category"] = category
        emitted["message"] = message

    monkeypatch.setattr("autoresearch.ui.desktop.telemetry.qCInfo", fake_qcinfo)

    telemetry = DesktopTelemetry()
    telemetry.emit("ui.test.event")

    assert "category" in emitted
    category = emitted["category"]
    assert category.categoryName() == DESKTOP_TELEMETRY_CATEGORY


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


def _install_instant_worker(monkeypatch: pytest.MonkeyPatch) -> None:
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


def _install_deferred_worker(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    class DeferredThreadPool:
        def __init__(self) -> None:
            self.worker = None

        def start(self, worker) -> None:
            self.worker = worker

    pool = DeferredThreadPool()

    monkeypatch.setattr(
        QtCore.QThreadPool,
        "globalInstance",
        staticmethod(lambda: pool),
    )

    def immediate_single_shot(_interval: int, receiver, slot=None) -> None:
        callback = slot or receiver
        callback()

    monkeypatch.setattr(QtCore.QTimer, "singleShot", staticmethod(immediate_single_shot))
    return {"pool": pool}


def _install_stub_configuration(
    monkeypatch: pytest.MonkeyPatch,
    *,
    raise_error: bool = False,
    exports: Mapping[str, bool] | None = None,
) -> None:
    class DummyLoader:
        def load_config(self) -> ConfigModel:
            return ConfigModel()

    class DummyOrchestrator:
        def run_query(self, query: str, config: ConfigModel) -> QueryResponse:
            if raise_error:
                raise RuntimeError("boom")
            metrics: Mapping[str, Any] = {"tokens": {"total": 3}}
            if exports is not None:
                metrics = {
                    **metrics,
                    "knowledge_graph": {"exports": dict(exports)},
                }
            return QueryResponse(
                query=query,
                answer="ok",
                citations=[],
                reasoning=[],
                metrics=metrics,
                warnings=[],
                claim_audits=[],
                task_graph=None,
                react_traces=[],
                state_id=None,
            )

    monkeypatch.setattr(main_window_module, "ConfigLoader", DummyLoader)
    monkeypatch.setattr(main_window_module, "Orchestrator", DummyOrchestrator)


def test_export_buttons_gated_during_query(
    qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_stub_configuration(monkeypatch, exports={"graphml": True})
    pool_ref = _install_deferred_worker(monkeypatch)

    window = AutoresearchMainWindow()
    qtbot.addWidget(window)

    assert window.export_manager is not None
    window.export_manager.set_available_exports({"graphml": True})
    export_buttons = [
        button
        for button in window.export_manager.findChildren(QPushButton)
        if button.text().startswith("Export")
    ]
    assert export_buttons
    initial_button = export_buttons[0]
    assert initial_button.isEnabled()

    assert window.query_panel is not None
    window.query_panel.set_query_text("Gate exports")
    window.query_panel.on_run_clicked()

    qtbot.waitUntil(lambda: pool_ref["pool"].worker is not None, timeout=500)
    assert not initial_button.isEnabled()

    worker = pool_ref["pool"].worker
    assert worker is not None
    worker.run()

    def _all_enabled() -> bool:
        buttons = [
            button
            for button in window.export_manager.findChildren(QPushButton)
            if button.text().startswith("Export")
        ]
        return bool(buttons) and all(button.isEnabled() for button in buttons)

    qtbot.waitUntil(_all_enabled, timeout=500)

    final_buttons = [
        button
        for button in window.export_manager.findChildren(QPushButton)
        if button.text().startswith("Export")
    ]
    assert final_buttons
    assert all(button.isEnabled() for button in final_buttons)


def test_main_window_emits_completed_telemetry(
    qtbot, monkeypatch: pytest.MonkeyPatch, telemetry_events
) -> None:
    _install_stub_configuration(monkeypatch)
    _install_instant_worker(monkeypatch)

    window = AutoresearchMainWindow()
    qtbot.addWidget(window)

    assert window.query_panel is not None
    window.query_panel.set_query_text("Telemetry flow")
    window.query_panel.on_run_clicked()

    qtbot.waitUntil(
        lambda: any(event == "ui.query.completed" for event, _ in telemetry_events),
        timeout=500,
    )

    submitted_payload = next(
        payload for event, payload in telemetry_events if event == "ui.query.submitted"
    )
    completed_payload = next(
        payload for event, payload in telemetry_events if event == "ui.query.completed"
    )

    assert submitted_payload["session_id"] == completed_payload["session_id"]
    assert completed_payload["query_length"] == len("Telemetry flow")
    assert completed_payload["duration_ms"] >= 0


def test_main_window_emits_failed_telemetry(
    qtbot, monkeypatch: pytest.MonkeyPatch, telemetry_events
) -> None:
    _install_stub_configuration(monkeypatch, raise_error=True)
    _install_instant_worker(monkeypatch)
    monkeypatch.setenv("AUTORESEARCH_SUPPRESS_DIALOGS", "1")

    window = AutoresearchMainWindow()
    qtbot.addWidget(window)

    assert window.query_panel is not None
    window.query_panel.set_query_text("Failure flow")
    window.query_panel.on_run_clicked()

    qtbot.waitUntil(
        lambda: any(event == "ui.query.failed" for event, _ in telemetry_events),
        timeout=500,
    )

    submitted_payload = next(
        payload for event, payload in telemetry_events if event == "ui.query.submitted"
    )
    failed_payload = next(
        payload for event, payload in telemetry_events if event == "ui.query.failed"
    )

    assert submitted_payload["session_id"] == failed_payload["session_id"]
    assert failed_payload["status"] == "failed"
    assert failed_payload["error_type"] == "RuntimeError"


def test_main_window_emits_cancelled_telemetry(
    qtbot,
    monkeypatch: pytest.MonkeyPatch,
    telemetry_events,
    capfd: pytest.CaptureFixture[str],
) -> None:
    _install_stub_configuration(monkeypatch)
    pool_ref = _install_deferred_worker(monkeypatch)
    monkeypatch.setenv("AUTORESEARCH_SUPPRESS_DIALOGS", "1")

    prompts: list[tuple[str, str, Any, Any]] = []

    def fake_question(
        self,
        title: str,
        message: str,
        buttons: Any,
        default: Any,
    ) -> int:
        prompts.append((title, message, buttons, default))
        self._log_dialog("question", title, message)
        return QMessageBox.Yes

    monkeypatch.setattr(AutoresearchMainWindow, "_ask_question", fake_question)

    window = AutoresearchMainWindow()
    qtbot.addWidget(window)

    assert window.query_panel is not None
    window.query_panel.set_query_text("Cancellation flow")
    window.query_panel.on_run_clicked()

    qtbot.waitUntil(lambda: pool_ref["pool"].worker is not None, timeout=500)
    qtbot.waitUntil(lambda: window.query_panel.cancel_button.isVisible(), timeout=500)
    qtbot.mouseClick(window.query_panel.cancel_button, Qt.LeftButton)

    qtbot.waitUntil(
        lambda: any(event == "ui.query.cancelled" for event, _ in telemetry_events),
        timeout=500,
    )

    captured = capfd.readouterr()
    assert "[QUESTION] Cancel running query" in captured.err
    assert prompts
    title, message, buttons, default = prompts[-1]
    assert title == "Cancel running query"
    assert "current query is still running" in message
    assert buttons == (QMessageBox.Yes | QMessageBox.No)
    assert default == QMessageBox.No

    submitted_payload = next(
        payload for event, payload in telemetry_events if event == "ui.query.submitted"
    )
    cancelled_payload = next(
        payload for event, payload in telemetry_events if event == "ui.query.cancelled"
    )

    assert submitted_payload["session_id"] == cancelled_payload["session_id"]
    assert cancelled_payload["status"] == "cancelled"
    assert not window.query_panel.is_busy()
    assert not window.progress_bar.isVisible()

    worker = pool_ref["pool"].worker
    assert worker is not None
    worker.run()

    assert not any(event == "ui.query.completed" for event, _ in telemetry_events)


def test_main_window_cancel_decline_keeps_worker_running(
    qtbot,
    monkeypatch: pytest.MonkeyPatch,
    telemetry_events,
    capfd: pytest.CaptureFixture[str],
) -> None:
    _install_stub_configuration(monkeypatch)
    pool_ref = _install_deferred_worker(monkeypatch)
    monkeypatch.setenv("AUTORESEARCH_SUPPRESS_DIALOGS", "1")

    prompts: list[tuple[str, str, Any, Any]] = []

    def fake_question(
        self,
        title: str,
        message: str,
        buttons: Any,
        default: Any,
    ) -> int:
        prompts.append((title, message, buttons, default))
        self._log_dialog("question", title, message)
        return QMessageBox.No

    monkeypatch.setattr(AutoresearchMainWindow, "_ask_question", fake_question)

    window = AutoresearchMainWindow()
    qtbot.addWidget(window)

    assert window.query_panel is not None
    window.query_panel.set_query_text("Keep running")
    window.query_panel.on_run_clicked()

    qtbot.waitUntil(lambda: pool_ref["pool"].worker is not None, timeout=500)
    qtbot.waitUntil(lambda: window.query_panel.cancel_button.isVisible(), timeout=500)
    qtbot.mouseClick(window.query_panel.cancel_button, Qt.LeftButton)

    captured = capfd.readouterr()
    assert "[QUESTION] Cancel running query" in captured.err
    assert prompts
    _, message, _, _ = prompts[-1]
    assert "current query is still running" in message

    assert window.is_query_running
    assert window.query_panel.is_busy()
    assert window.progress_bar.isVisible()
    assert pool_ref["pool"].worker is not None
    assert not any(event == "ui.query.cancelled" for event, _ in telemetry_events)

