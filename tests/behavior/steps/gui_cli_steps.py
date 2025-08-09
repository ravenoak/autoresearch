import subprocess

from pytest_bdd import scenario, then, when

from autoresearch.main import app as cli_app


@when("I run `autoresearch gui --port 8502 --no-browser`")
def run_gui_no_browser(
    cli_runner, bdd_context, monkeypatch, temp_config, isolate_network
):
    calls: list = []

    def fake_run(*a, **k):
        calls.append((a, k))
        return subprocess.CompletedProcess(a, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = cli_runner.invoke(
        cli_app, ["gui", "--port", "8502", "--no-browser"], catch_exceptions=False
    )
    bdd_context.update({"result": result, "run_calls": calls})


@when("I run `autoresearch gui --help`")
def run_gui_help(cli_runner, bdd_context, temp_config, isolate_network):
    result = cli_runner.invoke(cli_app, ["gui", "--help"], catch_exceptions=False)
    bdd_context["result"] = result


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""
    if "run_calls" in bdd_context:
        assert len(bdd_context["run_calls"]) == 1


@scenario("../features/gui_cli.feature", "Launch GUI without opening a browser")
def test_gui_no_browser():
    pass


@scenario("../features/gui_cli.feature", "Display help for GUI command")
def test_gui_help():
    pass
