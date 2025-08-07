# flake8: noqa
"""Monitor CLI behavior step implementations."""

from __future__ import annotations

import time
from pytest_bdd import scenario, when, then

from .common_steps import cli_app


@when('I run `autoresearch monitor`')
def run_monitor(
    monkeypatch,
    bdd_context,
    cli_runner,
    dummy_query_response,
    reset_global_registries,
):
    """Execute the monitor command once with deterministic metrics."""

    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: {"cpu_percent": 10.0, "memory_percent": 5.0},
    )
    result = cli_runner.invoke(cli_app, ["monitor"])
    bdd_context["monitor_result"] = result


@when('I run `autoresearch monitor -w`')
def run_monitor_watch(
    monkeypatch,
    bdd_context,
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

    monkeypatch.setattr(time, "sleep", fake_sleep)
    result = cli_runner.invoke(cli_app, ["monitor", "-w"])
    bdd_context["monitor_result"] = result
    bdd_context["sleep_calls"] = sleep_calls


@when('I run `autoresearch monitor` with metrics backend unavailable')
def run_monitor_backend_unavailable(
    monkeypatch,
    bdd_context,
    cli_runner,
    dummy_query_response,
    reset_global_registries,
):
    """Execute monitor command when metrics collection fails."""

    def fail() -> dict:
        raise RuntimeError("metrics backend unavailable")

    monkeypatch.setattr("autoresearch.monitor._collect_system_metrics", fail)
    result = cli_runner.invoke(cli_app, ["monitor"])
    bdd_context["monitor_result"] = result


@then("the monitor command should exit successfully")
def monitor_exit_successfully(bdd_context):
    result = bdd_context["monitor_result"]
    assert result.exit_code == 0
    assert result.stderr == ""


@then("the monitor output should show CPU and memory usage")
def monitor_output_metrics(bdd_context):
    output = bdd_context["monitor_result"].stdout
    assert "cpu_percent" in output
    assert "memory_percent" in output


@then("the monitor should refresh every second")
def monitor_refresh_interval(bdd_context):
    assert bdd_context.get("sleep_calls") == [1]


@then("the monitor command should exit with an error")
def monitor_exit_error(bdd_context):
    result = bdd_context["monitor_result"]
    assert result.exit_code != 0


@then("the monitor output should include a friendly metrics backend error message")
def monitor_error_message(bdd_context):
    output = bdd_context["monitor_result"].stdout + bdd_context["monitor_result"].stderr
    assert "metrics backend unavailable" in output.lower()


@scenario("../features/monitor_cli.feature", "Basic metric display")
def test_monitor_basic():
    """Scenario: Basic metric display."""
    pass


@scenario("../features/monitor_cli.feature", "Watch mode displays metrics continuously")
def test_monitor_watch():
    """Scenario: Watch mode displays metrics continuously."""
    pass


@scenario("../features/monitor_cli.feature", "Metrics backend unavailable")
def test_monitor_backend_unavailable():
    """Scenario: Metrics backend unavailable."""
    pass

