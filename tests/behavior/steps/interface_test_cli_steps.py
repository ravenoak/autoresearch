from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import scenario, then, when
from typer.testing import CliRunner

from autoresearch.main import app as cli_app
from tests.behavior.steps import BehaviorContext, get_cli_result, set_cli_result
from tests.behavior.utils import as_payload


@when('I run `autoresearch test_mcp --host 127.0.0.1 --port 8080`')
def run_test_mcp(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    temp_config: Any,
    isolate_network: None,
) -> None:
    """Execute the MCP interface test command successfully."""

    _ = temp_config

    class DummyClient:
        def __init__(self, host: str = "127.0.0.1", port: int = 8080) -> None:
            _ = (host, port)

        def run_test_suite(self) -> dict[str, Any]:
            return as_payload({"connection_test": {"status": "success"}})

    monkeypatch.setattr("autoresearch.main.app.MCPTestClient", DummyClient)
    monkeypatch.setattr("autoresearch.main.app.format_test_results", lambda _r, _f: "ok")
    result = cli_runner.invoke(
        cli_app,
        ["test_mcp", "--host", "127.0.0.1", "--port", "8080"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@when('I run `autoresearch test_mcp --port 9`')
def run_test_mcp_fail(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    temp_config: Any,
    isolate_network: None,
) -> None:
    """Execute the MCP test command with a failing connection."""

    _ = temp_config

    class FailingClient:
        def __init__(self, host: str = "127.0.0.1", port: int = 9) -> None:
            raise RuntimeError("connection failed")

    monkeypatch.setattr("autoresearch.main.app.MCPTestClient", FailingClient)
    result = cli_runner.invoke(
        cli_app,
        ["test_mcp", "--port", "9"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@when('I run `autoresearch test_a2a --host 127.0.0.1 --port 8765`')
def run_test_a2a(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    temp_config: Any,
    isolate_network: None,
) -> None:
    """Execute the A2A interface test command successfully."""

    _ = temp_config

    class DummyClient:
        def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
            _ = (host, port)

        def run_test_suite(self) -> dict[str, Any]:
            return as_payload({"connection_test": {"status": "success"}})

    monkeypatch.setattr("autoresearch.main.app.A2ATestClient", DummyClient)
    monkeypatch.setattr("autoresearch.main.app.format_test_results", lambda _r, _f: "ok")
    result = cli_runner.invoke(
        cli_app,
        ["test_a2a", "--host", "127.0.0.1", "--port", "8765"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@when('I run `autoresearch test_a2a --port 9`')
def run_test_a2a_fail(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    temp_config: Any,
    isolate_network: None,
) -> None:
    """Execute the A2A interface test command with a failure."""

    _ = temp_config

    class FailingClient:
        def __init__(self, host: str = "127.0.0.1", port: int = 9) -> None:
            raise RuntimeError("connection failed")

    monkeypatch.setattr("autoresearch.main.app.A2ATestClient", FailingClient)
    result = cli_runner.invoke(
        cli_app,
        ["test_a2a", "--port", "9"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@then('the CLI should exit successfully')
def cli_success(bdd_context: BehaviorContext) -> None:
    """Assert that the CLI invocation succeeded."""

    result = get_cli_result(bdd_context)
    assert result.exit_code == 0
    assert result.stderr == ""


@then('the CLI should exit with an error')
def cli_error(bdd_context: BehaviorContext) -> None:
    """Assert that the CLI invocation failed."""

    result = get_cli_result(bdd_context)
    assert result.exit_code != 0
    assert result.stderr != "" or result.exception is not None


@scenario('../features/interface_test_cli.feature', 'Run MCP interface tests')
def test_mcp_success() -> None:
    """Scenario: successfully run MCP interface tests."""


@scenario('../features/interface_test_cli.feature', 'Fail to connect to MCP server')
def test_mcp_failure() -> None:
    """Scenario: fail to connect to the MCP server."""


@scenario('../features/interface_test_cli.feature', 'Run A2A interface tests')
def test_a2a_success() -> None:
    """Scenario: successfully run A2A interface tests."""


@scenario('../features/interface_test_cli.feature', 'Fail to connect to A2A server')
def test_a2a_failure() -> None:
    """Scenario: fail to connect to the A2A server."""
