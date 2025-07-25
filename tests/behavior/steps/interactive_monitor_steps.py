# flake8: noqa
from pytest_bdd import scenario, when, then, parsers

from .common_steps import *  # noqa: F401,F403


@when(parsers.parse('I start `autoresearch monitor run` and enter "{text}"'))
def start_monitor(text, monkeypatch, bdd_context, cli_runner):
    responses = iter([text, "", "q"])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr("autoresearch.monitor.Prompt.ask", lambda *a, **k: next(responses))
    result = cli_runner.invoke(cli_app, ["monitor", "run"])
    bdd_context["monitor_result"] = result


@when('I run `autoresearch monitor metrics`')
def run_metrics(monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: {"cpu_percent": 10.0, "memory_percent": 5.0},
    )
    result = cli_runner.invoke(cli_app, ["monitor", "metrics"])
    bdd_context["monitor_result"] = result


@when('I run `autoresearch monitor graph`')
def run_graph(monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr(
        "autoresearch.monitor._collect_graph_data",
        lambda: {"A": ["B", "C"]},
    )
    result = cli_runner.invoke(cli_app, ["monitor", "graph"])
    bdd_context["monitor_result"] = result


@when('I run `autoresearch monitor graph --tui`')
def run_graph_tui(monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr(
        "autoresearch.monitor._collect_graph_data",
        lambda: {"A": ["B", "C"]},
    )
    result = cli_runner.invoke(cli_app, ["monitor", "graph", "--tui"])
    bdd_context["monitor_result"] = result


@when(parsers.parse('I run `autoresearch search "{query}" --visualize`'))
def run_search_visualize(query, monkeypatch, bdd_context, cli_runner):
    from autoresearch.orchestration.orchestrator import Orchestrator
    from autoresearch.models import QueryResponse

    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(
        "autoresearch.monitor._collect_graph_data",
        lambda: {"A": ["B"]},
    )

    def dummy_run_query(*args, **kwargs):
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    result = cli_runner.invoke(cli_app, ["search", query, "--visualize"])
    bdd_context["visual_result"] = result


@when('I run `autoresearch monitor resources --duration 1`')
def run_monitor_resources(monkeypatch, bdd_context, cli_runner):
    class DummyMetrics:
        def record_system_resources(self):
            pass

        def get_summary(self):
            return {
                "resource_usage": [
                    {
                        "timestamp": 0,
                        "cpu_percent": 10.0,
                        "memory_mb": 5.0,
                        "gpu_percent": 0.0,
                        "gpu_memory_mb": 0.0,
                    }
                ]
            }

    monkeypatch.setattr(
        "autoresearch.monitor.orch_metrics.OrchestrationMetrics", lambda: DummyMetrics()
    )
    monkeypatch.setattr("time.sleep", lambda *_: None)
    result = cli_runner.invoke(
        cli_app, ["monitor", "resources", "--duration", "1"]
    )
    bdd_context["monitor_result"] = result


@when('I run `autoresearch monitor start --interval 0.1`')
def run_monitor_start(monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr(
        "autoresearch.monitor.ResourceMonitor.start", lambda self, prometheus_port=None: None
    )
    monkeypatch.setattr("autoresearch.monitor.ResourceMonitor.stop", lambda self: None)
    monkeypatch.setattr("autoresearch.monitor.SystemMonitor.start", lambda self: None)
    monkeypatch.setattr("autoresearch.monitor.SystemMonitor.stop", lambda self: None)

    def _raise(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", _raise)
    result = cli_runner.invoke(cli_app, ["monitor", "start", "--interval", "0.1"])
    bdd_context["monitor_result"] = result


@then("the monitor should exit successfully")
def monitor_exit_successfully(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@then("the monitor output should display system metrics")
def monitor_output_contains_metrics(bdd_context):
    output = bdd_context["monitor_result"].stdout
    assert "System Metrics" in output
    assert "cpu_percent" in output
    assert "memory_percent" in output


@then("the monitor output should display graph data")
def monitor_output_contains_graph(bdd_context):
    output = bdd_context["monitor_result"].stdout
    assert "Knowledge Graph" in output
    assert "A" in output


@then("the search command should exit successfully")
def search_exit_successfully(bdd_context):
    assert bdd_context["visual_result"].exit_code == 0


@then("the search output should display graph data")
def search_output_contains_graph(bdd_context):
    output = bdd_context["visual_result"].stdout
    assert "Knowledge Graph" in output
    assert "Answer" in output


@then("the monitor output should display resource usage")
def monitor_output_contains_resources(bdd_context):
    output = bdd_context["monitor_result"].stdout
    assert "Resource Usage" in output
    assert "CPU %" in output


@then("the monitor output should indicate it started")
def monitor_output_started(bdd_context):
    output = bdd_context["monitor_result"].stdout
    assert "Monitoring started" in output


@scenario("../features/interactive_monitor.feature", "Interactive monitoring")
def test_interactive_monitor(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Exit immediately")
def test_monitor_exit_immediately(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Display metrics")
def test_monitor_metrics(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Display graph")
def test_monitor_graph(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Display TUI graph")
def test_monitor_graph_tui(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Visualize search results")
def test_search_visualization(bdd_context):
    assert bdd_context["visual_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Record resource usage")
def test_monitor_resources(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Start monitoring service")
def test_monitor_start_service(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0
