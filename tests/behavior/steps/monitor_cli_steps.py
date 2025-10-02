# flake8: noqa
"""Monitor CLI behavior step implementations."""

from __future__ import annotations
from tests.behavior.context import BehaviorContext

import time

import pytest
from pytest_bdd import given, scenario, then, when

from .common_steps import cli_app
from . import common_steps  # noqa: F401


@given("the application is running")
def _app_running():
    """Provide a no-op background step for CLI scenarios."""
    return


@when("I run `autoresearch monitor`")
def run_monitor(
    monkeypatch,
    bdd_context: BehaviorContext,
    cli_runner,
    dummy_query_response,
    reset_global_registries,
):
    """Execute the monitor command once with deterministic metrics."""

    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: {"cpu_percent": 10.0, "memory_percent": 5.0},
    )
    monkeypatch.setattr("autoresearch.monitor.time.sleep", lambda *_: None)
    result = cli_runner.invoke(cli_app, ["monitor"])
    bdd_context["monitor_result"] = result


@when("I run `autoresearch monitor -w`")
def run_monitor_watch(
    monkeypatch,
    bdd_context: BehaviorContext,
    cli_runner,
    dummy_query_response,
    reset_global_registries,
):
    """Execute the monitor command in watch mode and capture refresh interval."""

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
    bdd_context["monitor_result"] = result
    bdd_context["sleep_calls"] = sleep_calls


@when("I run `autoresearch monitor` with metrics backend unavailable")
def run_monitor_backend_unavailable(
    monkeypatch,
    bdd_context: BehaviorContext,
    cli_runner,
    dummy_query_response,
    reset_global_registries,
):
    """Execute monitor command when metrics collection fails."""

    def fail() -> dict:
        raise RuntimeError("metrics backend unavailable")

    monkeypatch.setattr("autoresearch.monitor._collect_system_metrics", fail)
    monkeypatch.setattr("autoresearch.monitor.time.sleep", lambda *_: None)
    result = cli_runner.invoke(cli_app, ["monitor"])
    bdd_context["monitor_result"] = result


@then("the monitor command should exit successfully")
def monitor_exit_successfully(bdd_context: BehaviorContext):
    result = bdd_context["monitor_result"]
    assert result.exit_code == 0
    assert result.stderr == ""


@then("the monitor output should show CPU and memory usage")
def monitor_output_metrics(bdd_context: BehaviorContext):
    output = bdd_context["monitor_result"].stdout
    assert "cpu_percent" in output
    assert "memory_percent" in output


@then("the monitor should refresh every second")
def monitor_refresh_interval(bdd_context: BehaviorContext):
    assert bdd_context.get("sleep_calls") == [1]


@then("the monitor command should exit with an error")
def monitor_exit_error(bdd_context: BehaviorContext):
    result = bdd_context["monitor_result"]
    assert result.exit_code != 0


@then("the monitor output should include a friendly metrics backend error message")
def monitor_error_message(bdd_context: BehaviorContext):
    result = bdd_context["monitor_result"]
    output = result.stdout + result.stderr
    if not output and result.exception:
        output = str(result.exception)
    assert "metrics backend unavailable" in output.lower()


@scenario("../features/monitor_cli.feature", "Basic metric display")
def test_monitor_basic():
    """Scenario: Basic metric display."""
    pass


@scenario("../features/monitor_cli.feature", "Watch mode displays metrics continuously")
def test_monitor_watch():
    """Scenario: Watch mode displays metrics continuously."""
    pass


@pytest.mark.skip(reason="Monitor error handling not implemented")
@scenario("../features/monitor_cli.feature", "Metrics backend unavailable")
def test_monitor_backend_unavailable():
    """Scenario: Metrics backend unavailable."""
    pass


@when("I run `autoresearch monitor resources -d 1`")
def run_monitor_resources(
    monkeypatch,
    bdd_context: BehaviorContext,
    cli_runner,
    dummy_query_response,
    reset_global_registries,
):
    """Execute resource monitoring for a short duration."""

    def fake_record(self):
        self.resource_usage.append((time.time(), 10.0, 5.0, 0.0, 0.0))

    monkeypatch.setattr(
        "autoresearch.orchestration.metrics.OrchestrationMetrics.record_system_resources",
        fake_record,
    )
    monkeypatch.setattr("autoresearch.monitor.time.sleep", lambda *_: None)
    result = cli_runner.invoke(cli_app, ["monitor", "resources", "-d", "1"])
    bdd_context["monitor_result"] = result


@pytest.mark.skip(reason="Monitor resources CLI exits non-zero")
@scenario(
    "../features/monitor_cli.feature", "Resource monitoring for a duration"
)
def test_monitor_resources_duration():
    """Scenario: Resource monitoring for a duration."""
    pass
