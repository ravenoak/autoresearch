# flake8: noqa
from pytest_bdd import scenario, when, then, parsers

from .common_steps import *  # noqa: F401,F403


@when(parsers.parse('I start `autoresearch monitor` and enter "{text}"'))
def start_monitor(text, monkeypatch, bdd_context):
    responses = iter([text, "", "q"])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    result = runner.invoke(cli_app, ["monitor"])
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
