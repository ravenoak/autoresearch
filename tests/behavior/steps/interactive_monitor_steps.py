from __future__ import annotations
from tests.behavior.utils import empty_metrics

from collections.abc import Iterator
from typing import Any

import pytest
from click.testing import CliRunner, Result
from pytest_bdd import parsers, scenario, then, when

from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from tests.behavior.context import BehaviorContext, get_required, set_value

from .common_steps import cli_app

pytest_plugins = ["tests.behavior.steps.common_steps"]


@when(parsers.parse('I start `autoresearch monitor run` and enter "{text}"'))
def start_monitor(
    text: str,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
) -> None:
    responses: Iterator[str] = iter([text, "", "q"])
    monkeypatch.setattr(
        "autoresearch.main.Prompt.ask", lambda *args, **kwargs: next(responses)
    )
    monkeypatch.setattr(
        "autoresearch.monitor.Prompt.ask", lambda *args, **kwargs: next(responses)
    )
    result = cli_runner.invoke(cli_app, ["monitor", "run"])
    set_value(bdd_context, "monitor_result", result)


@when('I run `autoresearch monitor metrics`')
def run_metrics(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
) -> None:
    metrics_payload: dict[str, float] = {"cpu_percent": 10.0, "memory_percent": 5.0}
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: metrics_payload,
    )
    result = cli_runner.invoke(cli_app, ["monitor", "metrics"])
    set_value(bdd_context, "monitor_result", result)


@when('I run `autoresearch monitor graph`')
def run_graph(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
) -> None:
    graph_data: dict[str, list[str]] = {"A": ["B", "C"]}
    monkeypatch.setattr(
        "autoresearch.monitor._collect_graph_data", lambda: graph_data
    )
    result = cli_runner.invoke(cli_app, ["monitor", "graph"])
    set_value(bdd_context, "monitor_result", result)


@when('I run `autoresearch monitor graph --tui`')
def run_graph_tui(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
) -> None:
    graph_data: dict[str, list[str]] = {"A": ["B", "C"]}
    monkeypatch.setattr(
        "autoresearch.monitor._collect_graph_data", lambda: graph_data
    )
    result = cli_runner.invoke(cli_app, ["monitor", "graph", "--tui"])
    set_value(bdd_context, "monitor_result", result)


@when(parsers.parse('I run `autoresearch search "{query}" --visualize`'))
def run_search_visualize(
    query: str,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
) -> None:
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    graph_data: dict[str, list[str]] = {"A": ["B"]}
    monkeypatch.setattr(
        "autoresearch.monitor._collect_graph_data", lambda: graph_data
    )

    def dummy_run_query(*_args: Any, **_kwargs: Any) -> QueryResponse:
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics=empty_metrics())

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    result = cli_runner.invoke(cli_app, ["search", query, "--visualize"])
    set_value(bdd_context, "visual_result", result)


@when('I run `autoresearch monitor resources --duration 1`')
def run_monitor_resources(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
) -> None:
    class DummyMetrics:
        def record_system_resources(self) -> None:
            return None

        def get_summary(self) -> dict[str, list[dict[str, float]]]:
            summary: dict[str, list[dict[str, float]]] = {
                "resource_usage": [
                    {
                        "timestamp": 0.0,
                        "cpu_percent": 10.0,
                        "memory_mb": 5.0,
                        "gpu_percent": 0.0,
                        "gpu_memory_mb": 0.0,
                    }
                ]
            }
            return summary

    monkeypatch.setattr(
        "autoresearch.monitor.orch_metrics.OrchestrationMetrics", lambda: DummyMetrics()
    )
    monkeypatch.setattr("time.sleep", lambda *_: None)
    result = cli_runner.invoke(
        cli_app, ["monitor", "resources", "--duration", "1"]
    )
    set_value(bdd_context, "monitor_result", result)


@when('I run `autoresearch monitor start --interval 0.1`')
def run_monitor_start(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
) -> None:
    monkeypatch.setattr(
        "autoresearch.monitor.ResourceMonitor.start",
        lambda self, prometheus_port=None: None,
    )
    monkeypatch.setattr("autoresearch.monitor.ResourceMonitor.stop", lambda self: None)
    monkeypatch.setattr("autoresearch.monitor.SystemMonitor.start", lambda self: None)
    monkeypatch.setattr("autoresearch.monitor.SystemMonitor.stop", lambda self: None)

    def _raise(_: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", _raise)
    result = cli_runner.invoke(cli_app, ["monitor", "start", "--interval", "0.1"])
    set_value(bdd_context, "monitor_result", result)


@then("the monitor should exit successfully")
def monitor_exit_successfully(bdd_context: BehaviorContext) -> None:
    result = get_required(bdd_context, "monitor_result", Result)
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@then("the monitor output should display system metrics")
def monitor_output_contains_metrics(bdd_context: BehaviorContext) -> None:
    output = get_required(bdd_context, "monitor_result", Result).stdout
    assert "System Metrics" in output
    assert "cpu_percent" in output
    assert "memory_percent" in output


@then("the monitor output should display graph data")
def monitor_output_contains_graph(bdd_context: BehaviorContext) -> None:
    output = get_required(bdd_context, "monitor_result", Result).stdout
    assert "Knowledge Graph" in output
    assert "A" in output


@then("the search command should exit successfully")
def search_exit_successfully(bdd_context: BehaviorContext) -> None:
    result = get_required(bdd_context, "visual_result", Result)
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@then("the search output should display graph data")
def search_output_contains_graph(bdd_context: BehaviorContext) -> None:
    output = get_required(bdd_context, "visual_result", Result).stdout
    assert "Knowledge Graph" in output
    assert "Answer" in output


@then("the monitor output should display resource usage")
def monitor_output_contains_resources(bdd_context: BehaviorContext) -> None:
    output = get_required(bdd_context, "monitor_result", Result).stdout
    assert "Resource Usage" in output
    assert "CPU %" in output


@then("the monitor output should indicate it started")
def monitor_output_started(bdd_context: BehaviorContext) -> None:
    output = get_required(bdd_context, "monitor_result", Result).stdout
    assert "Monitoring started" in output


@scenario("../features/interactive_monitor.feature", "Interactive monitoring")
def test_interactive_monitor(bdd_context: BehaviorContext) -> None:
    assert get_required(bdd_context, "monitor_result", Result).exit_code == 0


@scenario("../features/interactive_monitor.feature", "Exit immediately")
def test_monitor_exit_immediately(bdd_context: BehaviorContext) -> None:
    assert get_required(bdd_context, "monitor_result", Result).exit_code == 0


@scenario("../features/interactive_monitor.feature", "Display metrics")
def test_monitor_metrics(bdd_context: BehaviorContext) -> None:
    assert get_required(bdd_context, "monitor_result", Result).exit_code == 0


@scenario("../features/interactive_monitor.feature", "Display graph")
def test_monitor_graph(bdd_context: BehaviorContext) -> None:
    assert get_required(bdd_context, "monitor_result", Result).exit_code == 0


@scenario("../features/interactive_monitor.feature", "Display TUI graph")
def test_monitor_graph_tui(bdd_context: BehaviorContext) -> None:
    assert get_required(bdd_context, "monitor_result", Result).exit_code == 0


@scenario("../features/interactive_monitor.feature", "Visualize search results")
def test_search_visualization(bdd_context: BehaviorContext) -> None:
    assert get_required(bdd_context, "visual_result", Result).exit_code == 0


@scenario("../features/interactive_monitor.feature", "Record resource usage")
def test_monitor_resources(bdd_context: BehaviorContext) -> None:
    assert get_required(bdd_context, "monitor_result", Result).exit_code == 0


@scenario("../features/interactive_monitor.feature", "Start monitoring service")
def test_monitor_start_service(bdd_context: BehaviorContext) -> None:
    assert get_required(bdd_context, "monitor_result", Result).exit_code == 0
