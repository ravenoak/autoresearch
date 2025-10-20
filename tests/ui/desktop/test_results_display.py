"""Tests for the PySide6 desktop results display widget.

Spec: docs/specs/pyside-desktop.md
"""

from __future__ import annotations

import json
import time
from types import SimpleNamespace

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
    reason="Qt WebEngine is required for results display tests",
    exc_type=ImportError,
)

Qt = QtCore.Qt

import autoresearch.ui.desktop.results_display as results_display_module

pytestmark = pytest.mark.requires_ui


class DummyFormatter:
    """Stub output formatter used to avoid invoking the full rendering stack."""

    @staticmethod
    def render(result, output_format: str, *, depth: str = "standard") -> str:
        assert output_format == "markdown"
        assert depth in {"standard", "detailed"}
        return result.answer


@pytest.fixture(autouse=True)
def _patch_formatter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(results_display_module, "OutputFormatter", DummyFormatter)


def test_results_display_renders_views_and_enables_citation_controls(qtbot) -> None:
    display = results_display_module.ResultsDisplay()
    qtbot.addWidget(display)
    display.show()
    qtbot.wait(10)

    answer_sink: dict[str, str] = {}

    class _AnswerStub:
        def setHtml(self, html: str) -> None:  # noqa: N802 - Qt naming convention
            answer_sink["html"] = html

    display.answer_view = _AnswerStub()

    result = SimpleNamespace(
        answer=(
            "# Heading\n\nText with [trusted](https://example.com) link and "
            "[bad](ftp://invalid) URL.\n<script>alert('x')</script>\n"
            + "long paragraph " * 400
        ),
        citations=[
            {"title": "Example Source", "url": "https://example.com/doc"},
            "Inline citation https://another.example/page",
            {"label": "Unsafe", "url": "javascript:alert(1)"},
        ],
        reasoning=["Gather documents", "Synthesize findings"],
        metrics={
            "latency_s": 1.2,
            "knowledge_graph": {
                "graph": {"nodes": ["A", "B"], "edges": [["A", "B"]]},
                "exports": {"graphml": True, "graph_json": False},
            },
        },
        knowledge_graph=None,
    )

    start = time.perf_counter()
    display.display_results(result)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5
    assert "&lt;script" in answer_sink.get("html", "")
    assert "ftp://invalid" not in answer_sink.get("html", "")

    assert display.citations_list is not None
    assert display.citations_placeholder is not None
    assert display.citations_list.count() == 3
    assert not display.citations_placeholder.isVisible()

    first_item = display.citations_list.item(0)
    assert first_item is not None
    first_data = first_item.data(Qt.UserRole)
    assert isinstance(first_data, dict)
    assert first_data["url"] == "https://example.com/doc"

    assert display.open_source_button is not None
    assert display.copy_source_button is not None
    assert display.open_source_button.isEnabled()
    assert display.copy_source_button.isEnabled()

    assert display.knowledge_graph_view is not None
    assert display.knowledge_graph_view._graph_data is not None  # type: ignore[attr-defined]

    assert display.trace_view is not None
    trace_text = display.trace_view.toPlainText()
    assert "Step 1" in trace_text
    assert "latency_s" in trace_text

    assert display.metrics_dashboard is not None
    assert display.metrics_dashboard._metrics == result.metrics  # type: ignore[attr-defined]


def test_results_display_handles_missing_citations_gracefully(qtbot) -> None:
    display = results_display_module.ResultsDisplay()
    qtbot.addWidget(display)
    display.show()
    qtbot.wait(10)

    answer_sink: dict[str, str] = {}

    class _AnswerStub:
        def setHtml(self, html: str) -> None:  # noqa: N802 - Qt naming convention
            answer_sink["html"] = html

    display.answer_view = _AnswerStub()

    result = SimpleNamespace(
        answer="Plain text answer without markdown.",
        citations=[],
        reasoning=[],
        metrics={},
        knowledge_graph=None,
    )

    display.display_results(result)

    assert "Plain text answer" in answer_sink.get("html", "")

    assert display.citations_list is not None
    assert display.citations_placeholder is not None
    assert display.citations_list.count() == 0
    assert not display.citations_placeholder.isHidden()

    assert display.open_source_button is not None
    assert display.copy_source_button is not None
    assert not display.open_source_button.isEnabled()
    assert not display.copy_source_button.isEnabled()

    assert display.trace_view is not None
    assert "No reasoning" in display.trace_view.toPlainText()

    assert display.metrics_dashboard is not None
    assert display.metrics_dashboard._metrics == {}  # type: ignore[attr-defined]

    assert display.knowledge_graph_view is not None
    assert display.knowledge_graph_view._graph_data is None  # type: ignore[attr-defined]


def test_results_display_loads_graph_from_storage(monkeypatch, qtbot) -> None:
    display = results_display_module.ResultsDisplay()
    qtbot.addWidget(display)
    display.show()
    qtbot.wait(10)

    class _DummyGraph:
        def nodes(self):  # noqa: D401 - mimic networkx signature
            return ["Source", "Target"]

        def edges(self, keys=False, data=False):  # noqa: D401 - mimic networkx signature
            if keys and data:
                return [("Source", "Target", "rel", {"type": "connects"})]
            if data:
                return [("Source", "Target", {"type": "connects"})]
            return [("Source", "Target")]

    class _DummyStorage:
        @staticmethod
        def get_knowledge_graph(*, create: bool = True):  # noqa: D401 - mimic storage signature
            assert create is False
            return _DummyGraph()

    monkeypatch.setattr(results_display_module, "StorageManager", _DummyStorage)

    result = SimpleNamespace(
        answer="Graph answer",
        citations=[],
        reasoning=[],
        metrics={},
        knowledge_graph=None,
    )

    display.display_results(result)

    assert display.knowledge_graph_view is not None
    graph_data = display.knowledge_graph_view._graph_data  # type: ignore[attr-defined]
    assert graph_data is not None
    assert graph_data["nodes"] == ["Source", "Target"]
    assert any(edge[:2] == ["Source", "Target"] for edge in graph_data["edges"])


def test_results_display_uses_graph_json_export(qtbot) -> None:
    display = results_display_module.ResultsDisplay()
    qtbot.addWidget(display)
    display.show()
    qtbot.wait(10)

    graph_json = json.dumps({"nodes": ["Earth", "Moon"], "edges": [["Earth", "Moon", "orbits"]]})

    result = SimpleNamespace(
        answer="Graph answer",
        citations=[],
        reasoning=[],
        metrics={"knowledge_graph": {"exports": {"graph_json": graph_json}}},
        knowledge_graph=None,
    )

    display.display_results(result)

    assert display.knowledge_graph_view is not None
    graph_data = display.knowledge_graph_view._graph_data  # type: ignore[attr-defined]
    assert graph_data == {"nodes": ["Earth", "Moon"], "edges": [["Earth", "Moon", "orbits"]]}
