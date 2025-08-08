import threading
from unittest.mock import MagicMock

from pytest_bdd import scenario, then, when

from autoresearch.main import app as cli_app


@when("I run `autoresearch serve --help`")
def run_serve_help(cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["serve", "--help"])
    bdd_context["result"] = result


@when("I run `autoresearch serve-a2a --help`")
def run_a2a_help(cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["serve-a2a", "--help"])
    bdd_context["result"] = result


@when("I run `autoresearch serve-a2a`")
def run_a2a(cli_runner, monkeypatch, bdd_context):
    mock_interface = MagicMock()
    mock_ctor = MagicMock(return_value=mock_interface)
    monkeypatch.setattr("autoresearch.a2a_interface.A2AInterface", mock_ctor)
    monkeypatch.setattr(
        "autoresearch.main.app.time.sleep",
        lambda _x: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    result_container: dict = {}

    def invoke() -> None:
        result_container["result"] = cli_runner.invoke(cli_app, ["serve-a2a"])

    thread = threading.Thread(target=invoke)
    thread.start()
    thread.join()
    bdd_context.update(
        {
            "result": result_container["result"],
            "mock_interface": mock_interface,
            "mock_ctor": mock_ctor,
            "server_thread": thread,
        }
    )


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert "usage:" in result.stdout.lower()
    assert result.stderr == ""


@then("the A2A server should start and stop")
def a2a_started_and_stopped(bdd_context):
    result = bdd_context["result"]
    mock_interface = bdd_context["mock_interface"]
    mock_ctor = bdd_context["mock_ctor"]
    assert result.exit_code == 0
    assert "Starting A2A server" in result.stdout
    assert "Server stopped" in result.stdout
    assert mock_ctor.call_count == 1
    assert mock_interface.start.call_count == 1
    assert mock_interface.stop.call_count == 1
    assert not bdd_context["server_thread"].is_alive()
    assert result.stderr == ""


@scenario("../features/serve_commands.feature", "Display help for serve")
def test_serve_help():
    pass


@scenario("../features/serve_commands.feature", "Display help for serve-a2a")
def test_serve_a2a_help():
    pass


@scenario("../features/serve_commands.feature", "Start serve-a2a")
def test_serve_a2a_start():
    pass
