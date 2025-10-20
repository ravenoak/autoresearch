"""Integration tests for the PySide6 desktop application shell.

Spec: docs/specs/pyside-desktop.md
"""

from __future__ import annotations

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
pytest.importorskip(
    "PySide6.QtWebEngineWidgets",
    reason="Qt WebEngine is required for desktop integration tests",
    exc_type=ImportError,
)

Qt = QtCore.Qt

from PySide6.QtWidgets import QPushButton

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.reasoning import ReasoningMode
import autoresearch.ui.desktop.main_window as main_window_module
import autoresearch.ui.desktop.results_display as results_display_module

pytestmark = pytest.mark.requires_ui


class _ImmediateThreadPool:
    def start(self, worker) -> None:  # noqa: D401 - Qt-compatible signature
        worker.run()


class _ImmediateTimer:
    @staticmethod
    def singleShot(_interval: int, receiver, slot=None) -> None:  # noqa: D401
        callback = slot or receiver
        callback()


class DummyFormatter:
    """Formatter used to bypass markdown dependencies in tests."""

    @staticmethod
    def render(result, output_format: str, *, depth: str = "standard") -> str:
        assert output_format == "markdown"
        return result.answer


@pytest.fixture(autouse=True)
def _patch_global_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTORESEARCH_SUPPRESS_DIALOGS", "1")
    monkeypatch.setattr(results_display_module, "OutputFormatter", DummyFormatter)
    monkeypatch.setattr(main_window_module, "OutputFormatter", DummyFormatter, raising=False)
    monkeypatch.setattr(QtCore.QThreadPool, "globalInstance", staticmethod(lambda: _ImmediateThreadPool()))
    monkeypatch.setattr(QtCore.QTimer, "singleShot", staticmethod(_ImmediateTimer.singleShot))
    monkeypatch.setattr(main_window_module, "get_orchestration_metrics", lambda: None, raising=False)


def test_desktop_main_window_runs_query_end_to_end(qtbot, monkeypatch) -> None:
    captured: dict[str, object] = {}
    busy_transitions: list[bool] = []

    class DummyConfigLoader:
        def load_config(self) -> ConfigModel:
            return ConfigModel()

    class DummyOrchestrator:
        def run_query(self, query: str, config: ConfigModel) -> QueryResponse:
            captured["query"] = query
            captured["config"] = config
            return QueryResponse(
                query=query,
                answer="Structured response",
                citations=[{"title": "Doc", "url": "https://example.com"}],
                reasoning=["Step 1", "Step 2"],
                metrics={
                    "latency_s": 1.0,
                    "knowledge_graph": {
                        "graph": {"nodes": ["A"], "edges": []},
                        "exports": {"graphml": True},
                    },
                },
                warnings=[],
                claim_audits=[],
                task_graph=None,
                react_traces=[],
                state_id=None,
            )

    monkeypatch.setattr(main_window_module, "ConfigLoader", DummyConfigLoader)
    monkeypatch.setattr(main_window_module, "Orchestrator", DummyOrchestrator)

    original_set_busy = main_window_module.QueryPanel.set_busy

    def _recording_set_busy(self, is_busy: bool) -> None:
        busy_transitions.append(is_busy)
        original_set_busy(self, is_busy)

    monkeypatch.setattr(
        main_window_module.QueryPanel,
        "set_busy",
        _recording_set_busy,
        raising=False,
    )

    window = main_window_module.AutoresearchMainWindow()
    qtbot.addWidget(window)

    assert window.query_panel is not None
    assert window.results_display is not None
    assert window.progress_bar is not None

    window.query_panel.set_query_text("How do dialectical agents coordinate?")
    window.query_panel.reasoning_mode_combo.setCurrentText("direct")
    window.query_panel.loops_spinbox.setValue(4)

    qtbot.mouseClick(window.query_panel.run_button, Qt.LeftButton)

    qtbot.waitUntil(lambda: window.results_display.current_result is not None, timeout=1000)

    assert busy_transitions == [True, False]

    assert captured["query"] == "How do dialectical agents coordinate?"
    config = captured["config"]
    assert isinstance(config, ConfigModel)
    assert config.loops == 4
    assert config.reasoning_mode == ReasoningMode.DIRECT

    assert window.progress_bar.isVisible() is False
    assert window.statusBar().currentMessage() == "Query completed"

    assert window.query_panel.query_input.isEnabled()
    assert window.query_panel.reasoning_mode_combo.isEnabled()
    assert window.query_panel.loops_spinbox.isEnabled()
    assert window.query_panel.run_button.isEnabled()

    result = window.results_display.current_result
    assert isinstance(result, QueryResponse)
    assert result.answer == "Structured response"

    assert window.results_display.citations_list is not None
    assert window.results_display.citations_list.count() == 1

    assert window.session_manager is not None
    assert window.session_manager._list.count() >= 1  # type: ignore[attr-defined]

    assert window.export_manager is not None
    active_exports = [widget.text() for widget in window.export_manager.findChildren(QPushButton)]
    assert any("Graphml" in text for text in active_exports)

    assert window.results_display.trace_view is not None
    assert "Step 1" in window.results_display.trace_view.toPlainText()

    assert window.results_display.metrics_dashboard is not None
    assert window.results_display.metrics_dashboard._metrics  # type: ignore[attr-defined]

    assert window.results_display.knowledge_graph_view is not None
    graph_data = window.results_display.knowledge_graph_view._graph_data  # type: ignore[attr-defined]
    assert graph_data is not None
    assert graph_data.get("nodes") == ["A"]
