from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import scenario, then, when
from typer.testing import CliRunner

from autoresearch.main import app as cli_app
from tests.behavior.steps import (
    BehaviorContext,
    PayloadDict,
    get_cli_result,
    get_required,
    set_cli_result,
    store_payload,
)


@when("I run `autoresearch gui --port 8502 --no-browser`")
def run_gui_no_browser(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    temp_config: Path,
    isolate_network: None,
) -> None:
    """Simulate running the GUI command without launching a browser."""

    _ = temp_config
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[object]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = cli_runner.invoke(
        cli_app,
        ["gui", "--port", "8502", "--no-browser"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)
    store_payload(bdd_context, "gui_invocation", run_calls=calls)


@when("I run `autoresearch gui --help`")
def run_gui_help(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    temp_config: Path,
    isolate_network: None,
) -> None:
    """Invoke the CLI help output for the GUI command."""

    _ = temp_config
    result = cli_runner.invoke(cli_app, ["gui", "--help"], catch_exceptions=False)
    set_cli_result(bdd_context, result)


@when("I run `autoresearch gui --port not-a-number`")
def run_gui_invalid_port(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    temp_config: Path,
    isolate_network: None,
) -> None:
    """Invoke the CLI with an invalid port argument."""

    _ = temp_config
    result = cli_runner.invoke(
        cli_app,
        ["gui", "--port", "not-a-number"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@then("the CLI should exit successfully")
def cli_success(bdd_context: BehaviorContext) -> None:
    """Ensure the CLI invocation succeeded and captured run calls."""

    result = get_cli_result(bdd_context)
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""
    payload = get_required(bdd_context, "gui_invocation", PayloadDict)
    if "run_calls" in payload:
        assert len(payload["run_calls"]) == 1


@scenario("../features/gui_cli.feature", "Launch GUI without opening a browser")
def test_gui_no_browser() -> None:
    """Scenario: run the GUI command without opening a browser."""


@scenario("../features/gui_cli.feature", "Display help for GUI command")
def test_gui_help() -> None:
    """Scenario: display CLI help for the GUI command."""


@scenario("../features/gui_cli.feature", "Launch GUI with invalid port")
def test_gui_invalid_port() -> None:
    """Scenario: fail when providing an invalid port."""
