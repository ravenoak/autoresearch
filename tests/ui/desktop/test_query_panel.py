"""Tests for the PySide6 desktop query panel widget.

Spec: docs/specs/pyside-desktop.md
"""

from __future__ import annotations

import time

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

from autoresearch.ui.desktop.query_panel import QueryPanel

pytestmark = pytest.mark.requires_ui


def test_query_panel_emits_signal_and_updates_configuration(qtbot) -> None:
    panel = QueryPanel()
    qtbot.addWidget(panel)
    panel.show()
    qtbot.waitActive(panel)

    emitted: list[str] = []
    panel.query_submitted.connect(emitted.append)

    panel.set_query_text("  Dialectical reasoning pathways  ")
    assert panel.query_input is not None
    assert panel.reasoning_mode_combo is not None
    assert panel.loops_spinbox is not None
    assert panel.run_button is not None

    panel.reasoning_mode_combo.setCurrentText("direct")
    qtbot.wait(10)
    panel.loops_spinbox.setValue(4)

    panel.run_button.setFocus()
    qtbot.keyClick(panel.run_button, Qt.Key_Space)

    assert emitted == ["Dialectical reasoning pathways"]

    configuration = panel.get_configuration()
    assert configuration["loops"] == 4
    assert configuration["reasoning_mode"] == panel.reasoning_mode_combo.currentText()


def test_query_panel_supports_keyboard_focus_traversal(qtbot) -> None:
    panel = QueryPanel()
    qtbot.addWidget(panel)
    panel.show()
    qtbot.waitActive(panel)

    assert panel.query_input is not None
    assert panel.reasoning_mode_combo is not None
    assert panel.loops_spinbox is not None
    assert panel.run_button is not None

    panel.focus_query_input()
    qtbot.wait(10)
    assert panel.query_input.hasFocus()

    assert panel.focusNextChild()
    assert panel.reasoning_mode_combo.hasFocus()

    assert panel.focusNextChild()
    assert panel.loops_spinbox.hasFocus()

    assert panel.focusNextChild()
    assert panel.run_button.hasFocus()


def test_query_panel_handles_long_text_without_truncation(qtbot) -> None:
    panel = QueryPanel()
    qtbot.addWidget(panel)

    assert panel.query_input is not None

    long_text = "strategic foresight " * 400
    start = time.perf_counter()
    panel.set_query_text(long_text)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.3
    assert panel.query_input.toPlainText().strip().startswith("strategic foresight")
    assert panel.query_input.document().characterCount() >= len(long_text)

    panel.clear_query()
    assert panel.query_input.toPlainText() == ""


def test_query_panel_busy_state_disables_controls_and_restores_focus(qtbot) -> None:
    panel = QueryPanel()
    qtbot.addWidget(panel)
    panel.show()
    qtbot.waitActive(panel)

    assert panel.query_input is not None
    assert panel.reasoning_mode_combo is not None
    assert panel.loops_spinbox is not None
    assert panel.run_button is not None

    panel.loops_spinbox.setFocus()
    qtbot.wait(10)
    assert panel.loops_spinbox.hasFocus()

    panel.set_busy(True)

    assert not panel.query_input.isEnabled()
    assert not panel.reasoning_mode_combo.isEnabled()
    assert not panel.loops_spinbox.isEnabled()
    assert not panel.run_button.isEnabled()

    panel.set_busy(False)

    assert panel.query_input.isEnabled()
    assert panel.reasoning_mode_combo.isEnabled()
    assert panel.loops_spinbox.isEnabled()
    assert panel.run_button.isEnabled()

    qtbot.waitUntil(lambda: panel.loops_spinbox.hasFocus(), timeout=200)
