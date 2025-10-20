from __future__ import annotations

from importlib import import_module
from typing import Any, cast

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pytest_bdd import given, parsers, scenario, then, when

from tests.behavior.context import (
    BehaviorContext,
    DesktopRuntimeMocks,
    desktop_runtime,
    get_required,
    set_value,
)

pytest_plugins = ["tests.behavior.steps.common_steps"]

pytestmark = pytest.mark.requires_ui


@scenario("../features/pyside6_desktop.feature", "Launching the PySide6 desktop shell")
def test_launch_desktop_shell() -> None:
    """BDD scenario ensuring the desktop shell starts cleanly."""


@scenario(
    "../features/pyside6_desktop.feature",
    "Submitting a query and reviewing results",
)
def test_submit_query_and_review_results() -> None:
    """BDD scenario covering the end-to-end Phase 1 desktop query flow."""


@scenario(
    "../features/pyside6_desktop.feature",
    "Cancelling a running query after a worker error",
)
def test_cancel_running_query_after_error() -> None:
    """BDD scenario exercising the cancellation and error recovery path."""


@given("the PySide6 desktop runtime is stubbed")
def stub_desktop_runtime(
    monkeypatch: MonkeyPatch, bdd_context: BehaviorContext
) -> Any:
    with desktop_runtime(monkeypatch) as runtime:
        set_value(bdd_context, "desktop_runtime", runtime)
        yield


@when("I launch the PySide6 desktop shell")
def launch_desktop_shell(bdd_context: BehaviorContext) -> None:
    runtime = get_required(bdd_context, "desktop_runtime", DesktopRuntimeMocks)
    import_module("autoresearch.ui.desktop.main")
    from autoresearch.ui.desktop import main as desktop_main

    exit_code = desktop_main.main()
    set_value(bdd_context, "desktop_exit_code", exit_code)
    window = runtime.latest_window()
    if window is not None:
        set_value(bdd_context, "desktop_window", window)


@when(parsers.parse('I submit "{query}" through the desktop query panel'))
def submit_desktop_query(bdd_context: BehaviorContext, query: str) -> None:
    window = get_required(bdd_context, "desktop_window")
    response = window.submit_query(query)
    set_value(bdd_context, "desktop_last_query", query)
    set_value(bdd_context, "desktop_query_response", response)


@when(parsers.parse('I stage a running desktop query for "{query}"'))
def stage_running_desktop_query(bdd_context: BehaviorContext, query: str) -> None:
    window = get_required(bdd_context, "desktop_window")
    window.stage_running_query(query)
    set_value(bdd_context, "desktop_last_query", query)


@when(parsers.parse('the desktop worker will fail with "{error_code}"'))
def configure_desktop_worker_failure(
    bdd_context: BehaviorContext, error_code: str
) -> None:
    window = get_required(bdd_context, "desktop_window")
    window.set_pending_failure(error_code)


@when("I request to cancel the running desktop query")
def request_desktop_cancellation(bdd_context: BehaviorContext) -> None:
    window = get_required(bdd_context, "desktop_window")
    window.request_cancel()


@when("I confirm the cancellation prompt")
def confirm_desktop_cancellation(bdd_context: BehaviorContext) -> None:
    window = get_required(bdd_context, "desktop_window")
    window.confirm_cancel()


@when("the desktop worker failure is processed")
def process_desktop_worker_failure(bdd_context: BehaviorContext) -> None:
    window = get_required(bdd_context, "desktop_window")
    window.resolve_pending_failure()


@then("the desktop main window is shown")
def assert_window_shown(bdd_context: BehaviorContext) -> None:
    window = get_required(bdd_context, "desktop_window")
    assert getattr(window, "visible", False)


@then("the QApplication event loop starts")
def assert_event_loop_started(bdd_context: BehaviorContext) -> None:
    runtime = get_required(bdd_context, "desktop_runtime", DesktopRuntimeMocks)
    app = runtime.apps[-1]
    assert getattr(app, "exec_call_count", 0) >= 1
    assert get_required(bdd_context, "desktop_exit_code") == 0


@then("the desktop query controls are disabled while the query runs")
def assert_controls_disabled_order(bdd_context: BehaviorContext) -> None:
    window = get_required(bdd_context, "desktop_window")
    events = list(getattr(window, "events", []))
    disabled_index = next(i for i, event in enumerate(events) if event == ("controls", "disabled"))
    results_index = next(i for i, event in enumerate(events) if event[0] == "results")
    enabled_index = next(i for i, event in enumerate(events) if event == ("controls", "enabled"))
    assert disabled_index < results_index < enabled_index


@then("the orchestrator receives the submitted query")
def assert_orchestrator_invoked(bdd_context: BehaviorContext) -> None:
    window = get_required(bdd_context, "desktop_window")
    query = get_required(bdd_context, "desktop_last_query", str)
    window.orchestrator.run_query.assert_called_once_with(query)


@then("I see the synthesized desktop results")
def assert_results_visible(bdd_context: BehaviorContext) -> None:
    response = get_required(bdd_context, "desktop_query_response")
    assert response is not None
    assert cast(str, response.answer).startswith("Synthesized desktop response")
    assert response.citations
    assert response.reasoning


@then("the cancellation confirmation prompt is shown")
def assert_cancellation_prompt(bdd_context: BehaviorContext) -> None:
    runtime = get_required(
        bdd_context, "desktop_runtime", DesktopRuntimeMocks
    )
    assert runtime.warning_calls, "No cancellation prompt was recorded."
    title, message = runtime.warning_calls[-1]
    assert title == "Cancel query?"
    assert "Cancel the active desktop query?" in message


@then("the desktop worker receives a cancel signal")
def assert_worker_cancelled(bdd_context: BehaviorContext) -> None:
    window = get_required(bdd_context, "desktop_window")
    assert ("cancel", "requested") in window.worker_events


@then("the desktop status bar returns to idle")
def assert_status_bar_idle(bdd_context: BehaviorContext) -> None:
    window = get_required(bdd_context, "desktop_window")
    assert window.status_bar_message == "Idle"
    assert window.status_history[-1] == "Idle"


@then(parsers.parse('the desktop shows a critical error notice for "{error_code}"'))
def assert_error_notice(bdd_context: BehaviorContext, error_code: str) -> None:
    runtime = get_required(
        bdd_context, "desktop_runtime", DesktopRuntimeMocks
    )
    assert runtime.critical_calls, "No error notice was recorded."
    title, message = runtime.critical_calls[-1]
    assert title == "Query failed"
    assert error_code in message
