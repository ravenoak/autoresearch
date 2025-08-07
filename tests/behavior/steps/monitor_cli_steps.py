# flake8: noqa
from pytest_bdd import scenario, when, then, parsers

from .common_steps import app_running, app_running_with_default, application_running, cli_app


@when('I run `autoresearch monitor`')
def run_single_metrics(monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: {"cpu_percent": 10.0, "memory_percent": 5.0},
    )
    result = cli_runner.invoke(cli_app, ["monitor"])
    bdd_context["monitor_result"] = result


@when('I run `autoresearch monitor -w`')
def watch_metrics(monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics",
        lambda: {"cpu_percent": 10.0, "memory_percent": 5.0},
    )
    def _raise(*args, **kwargs):
        raise KeyboardInterrupt()
    monkeypatch.setattr("time.sleep", _raise)
    result = cli_runner.invoke(cli_app, ["monitor", "-w"])
    bdd_context["monitor_result"] = result


@when('I run `autoresearch monitor --invalid`')
def monitor_invalid_flag(bdd_context, cli_runner):
    result = cli_runner.invoke(cli_app, ["monitor", "--invalid"])
    bdd_context["monitor_result"] = result


@when(parsers.parse('I start `autoresearch monitor run` in "{mode}" mode and enter "{text}"'))
def start_monitor_mode(mode, text, monkeypatch, bdd_context, cli_runner):
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.orchestration.orchestrator import Orchestrator
    from autoresearch.models import QueryResponse

    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: ConfigModel(loops=1, output_format="json", reasoning_mode=mode),
    )
    responses = iter([text, "", "q"])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr("autoresearch.monitor.Prompt.ask", lambda *a, **k: next(responses))

    def dummy_run(query, config, callbacks=None):
        assert config.reasoning_mode == mode
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run)
    result = cli_runner.invoke(cli_app, ["monitor", "run"])
    bdd_context["monitor_result"] = result


@when('I start `autoresearch monitor run` with a failing query')
def start_monitor_failure(monkeypatch, bdd_context, cli_runner):
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.orchestration.orchestrator import Orchestrator

    monkeypatch.setattr(
        ConfigLoader, "load_config", lambda self: ConfigModel(loops=1, output_format="json")
    )
    responses = iter(["fail", "q"])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr("autoresearch.monitor.Prompt.ask", lambda *a, **k: next(responses))

    def failing_run(*args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(Orchestrator, "run_query", failing_run)
    result = cli_runner.invoke(cli_app, ["monitor", "run"])
    bdd_context["monitor_result"] = result


@then("the monitor command should exit successfully")
def monitor_exit_successfully(bdd_context):
    result = bdd_context["monitor_result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@then("the monitor output should display system metrics")
def monitor_output_metrics(bdd_context):
    output = bdd_context["monitor_result"].stdout
    assert "System Metrics" in output
    assert "cpu_percent" in output
    assert "memory_percent" in output


@then("the monitor command should exit with an error")
def monitor_exit_with_error(bdd_context):
    result = bdd_context["monitor_result"]
    assert result.exit_code != 0
    assert result.stderr != ""


@then("the monitor output should include an invalid option message")
def monitor_invalid_message(bdd_context):
    output = bdd_context["monitor_result"].stdout + bdd_context["monitor_result"].stderr
    assert "No such option" in output


@then("the monitor output should contain an error message")
def monitor_output_error(bdd_context):
    output = bdd_context["monitor_result"].stdout
    assert "Error:" in output


@scenario("../features/monitor_cli.feature", "Display single-run metrics")
def test_monitor_single_run(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/monitor_cli.feature", "Watch metrics continuously")
def test_monitor_watch(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/monitor_cli.feature", "Handle invalid flag")
def test_monitor_invalid_flag(bdd_context):
    assert bdd_context["monitor_result"].exit_code != 0


@scenario("../features/monitor_cli.feature", "Monitor run supports <mode> reasoning")
def test_monitor_run_modes(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0


@scenario("../features/monitor_cli.feature", "Recover from orchestrator errors")
def test_monitor_error_recovery(bdd_context):
    assert bdd_context["monitor_result"].exit_code == 0
