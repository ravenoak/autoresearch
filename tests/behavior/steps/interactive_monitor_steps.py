# flake8: noqa
from pytest_bdd import scenario, when, then, parsers

from .common_steps import *  # noqa: F401,F403


@when(parsers.parse('I start `autoresearch monitor run` and enter "{text}"'))
def start_monitor(text, monkeypatch, bdd_context):
    responses = iter([text, "", "q"])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr("autoresearch.monitor.Prompt.ask", lambda *a, **k: next(responses))
    result = runner.invoke(cli_app, ["monitor", "run"])
    bdd_context["monitor_result"] = result


@when('I run `autoresearch monitor metrics`')
def run_metrics(monkeypatch, bdd_context):
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: {"cpu_percent": 10.0, "memory_percent": 5.0},
    )
    result = runner.invoke(cli_app, ["monitor", "metrics"])
    bdd_context["monitor_result"] = result


@then("the monitor should exit successfully")
def monitor_exit_successfully(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Interactive monitoring")
def test_interactive_monitor(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Exit immediately")
def test_monitor_exit_immediately(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/interactive_monitor.feature", "Display metrics")
def test_monitor_metrics(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0
