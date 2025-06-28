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
    assert "A" in output


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


@scenario("../features/interactive_monitor.feature", "Visualize search results")
def test_search_visualization(bdd_context):
    assert bdd_context["visual_result"].exit_code == 0
