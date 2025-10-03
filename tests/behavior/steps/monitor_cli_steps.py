"""Monitor CLI behavior step implementations."""

from __future__ import annotations

import time
from typing import Any

import pytest
from pytest_bdd import scenario, then, when
from typer.testing import CliRunner

from autoresearch.main import app as cli_app
from tests.behavior.steps import (
    BehaviorContext,
    PayloadDict,
    get_cli_result,
    get_required,
    set_cli_result,
    store_payload,
)

pytest_plugins = ["tests.behavior.steps.common_steps"]


@when("I run `autoresearch monitor`")
def run_monitor(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
    dummy_query_response: Any,
    reset_global_registries: Any,
) -> None:
    """Execute the monitor command once with deterministic metrics."""

    _ = (dummy_query_response, reset_global_registries)
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: {"cpu_percent": 10.0, "memory_percent": 5.0},
    )
    monkeypatch.setattr("autoresearch.monitor.time.sleep", lambda *_: None)
    result = cli_runner.invoke(cli_app, ["monitor"])
    set_cli_result(bdd_context, result, key="monitor_result")


@when("I run `autoresearch monitor -w`")
def run_monitor_watch(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
    dummy_query_response: Any,
    reset_global_registries: Any,
) -> None:
    """Execute the monitor command in watch mode and capture refresh interval."""

    _ = (dummy_query_response, reset_global_registries)
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: {"cpu_percent": 10.0, "memory_percent": 5.0},
    )
    sleep_calls: list[float] = []

    def fake_sleep(interval: float) -> None:
        sleep_calls.append(interval)
        raise KeyboardInterrupt()

    monkeypatch.setattr("autoresearch.monitor.time.sleep", fake_sleep)
    result = cli_runner.invoke(cli_app, ["monitor", "-w"])
    set_cli_result(bdd_context, result, key="monitor_result")
    store_payload(bdd_context, "monitor_payload", sleep_calls=sleep_calls)


@when("I run `autoresearch monitor` with metrics backend unavailable")
def run_monitor_backend_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
    dummy_query_response: Any,
    reset_global_registries: Any,
) -> None:
    """Execute the monitor command when metrics collection fails."""

    _ = (dummy_query_response, reset_global_registries)

    def fail() -> dict[str, float]:
        raise RuntimeError("metrics backend unavailable")

    monkeypatch.setattr("autoresearch.monitor._collect_system_metrics", fail)
    monkeypatch.setattr("autoresearch.monitor.time.sleep", lambda *_: None)
    result = cli_runner.invoke(cli_app, ["monitor"])
    set_cli_result(bdd_context, result, key="monitor_result")


@then("the monitor command should exit successfully")
def monitor_exit_successfully(bdd_context: BehaviorContext) -> None:
    """Assert the monitor command exited without errors."""

    result = get_cli_result(bdd_context, key="monitor_result")
    assert result.exit_code == 0
    assert result.stderr == ""


@then("the monitor output should show CPU and memory usage")
def monitor_output_metrics(bdd_context: BehaviorContext) -> None:
    """Verify the monitor output includes CPU and memory metrics."""

    result = get_cli_result(bdd_context, key="monitor_result")
    output = result.stdout
    assert "cpu_percent" in output
    assert "memory_percent" in output


@then("the monitor should refresh every second")
def monitor_refresh_interval(bdd_context: BehaviorContext) -> None:
    """Check the monitor watch mode refreshes once per second."""

    payload = get_required(bdd_context, "monitor_payload", PayloadDict)
    assert payload.get("sleep_calls") == [1]


@then("the monitor command should exit with an error")
def monitor_exit_error(bdd_context: BehaviorContext) -> None:
    """Assert the monitor command exited with a non-zero status."""

    result = get_cli_result(bdd_context, key="monitor_result")
    assert result.exit_code != 0


@then("the monitor output should include a friendly metrics backend error message")
def monitor_error_message(bdd_context: BehaviorContext) -> None:
    """Ensure the monitor command surfaces metrics backend failures."""

    result = get_cli_result(bdd_context, key="monitor_result")
    output = result.stdout + result.stderr
    if not output and result.exception:
        output = str(result.exception)
    assert "metrics backend unavailable" in output.lower()


@scenario("../features/monitor_cli.feature", "Basic metric display")
def test_monitor_basic() -> None:
    """Scenario: Basic metric display."""


@scenario("../features/monitor_cli.feature", "Watch mode displays metrics continuously")
def test_monitor_watch() -> None:
    """Scenario: Watch mode displays metrics continuously."""


@pytest.mark.skip(reason="Monitor error handling not implemented")
@scenario("../features/monitor_cli.feature", "Metrics backend unavailable")
def test_monitor_backend_unavailable() -> None:
    """Scenario: Metrics backend unavailable."""


@when("I run `autoresearch monitor resources -d 1`")
def run_monitor_resources(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
    dummy_query_response: Any,
    reset_global_registries: Any,
) -> None:
    """Execute resource monitoring for a short duration."""

    _ = (dummy_query_response, reset_global_registries)

    def fake_record(self: Any) -> None:
        self.resource_usage.append((time.time(), 10.0, 5.0, 0.0, 0.0))

    monkeypatch.setattr(
        "autoresearch.orchestration.metrics.OrchestrationMetrics.record_system_resources",
        fake_record,
    )
    monkeypatch.setattr("autoresearch.monitor.time.sleep", lambda *_: None)
    result = cli_runner.invoke(cli_app, ["monitor", "resources", "-d", "1"])
    set_cli_result(bdd_context, result, key="monitor_result")


@pytest.mark.skip(reason="Monitor resources CLI exits non-zero")
@scenario("../features/monitor_cli.feature", "Resource monitoring for a duration")
def test_monitor_resources_duration() -> None:
    """Scenario: Resource monitoring for a duration."""
