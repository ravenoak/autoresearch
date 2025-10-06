# mypy: ignore-errors
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import scenario, then, when
from typer.testing import CliRunner

from autoresearch.main import app as cli_app
from tests.behavior.steps import BehaviorContext, get_cli_result, set_cli_result

pytest_plugins = ["tests.behavior.steps.common_steps"]


@when('I run `autoresearch sparql "SELECT ?s WHERE { ?s a <http://example.com/B> }"`')
def run_sparql_query(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    temp_config: Path,
    isolate_network: None,
) -> None:
    """Execute a SPARQL query through the CLI."""

    _ = temp_config
    monkeypatch.setattr("autoresearch.main.app._cli_sparql", lambda *_a, **_k: None)
    result = cli_runner.invoke(
        cli_app,
        ["sparql", "SELECT ?s WHERE { ?s a <http://example.com/B> }"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@when('I run `autoresearch sparql "INVALID QUERY"`')
def run_sparql_invalid(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    temp_config: Path,
    isolate_network: None,
) -> None:
    """Execute a SPARQL command that raises an error."""

    _ = temp_config

    def _raise(*_a: Any, **_k: Any) -> None:
        raise ValueError("invalid")

    monkeypatch.setattr("autoresearch.main.app._cli_sparql", _raise)
    result = cli_runner.invoke(cli_app, ["sparql", "INVALID QUERY"], catch_exceptions=False)
    set_cli_result(bdd_context, result)


@then('the CLI should exit successfully')
def cli_success(bdd_context: BehaviorContext) -> None:
    """Assert the SPARQL command succeeded."""

    result = get_cli_result(bdd_context)
    assert result.exit_code == 0
    assert result.stderr == ""


@then('the CLI should exit with an error')
def cli_error(bdd_context: BehaviorContext) -> None:
    """Assert the SPARQL command failed as expected."""

    result = get_cli_result(bdd_context)
    assert result.exit_code != 0
    assert result.stderr != "" or result.exception is not None


@scenario('../features/sparql_cli.feature', 'Execute a SPARQL query with reasoning')
def test_sparql_success() -> None:
    """Scenario: execute a SPARQL query with reasoning."""


@scenario('../features/sparql_cli.feature', 'Invalid SPARQL query')
def test_sparql_invalid() -> None:
    """Scenario: SPARQL command fails when the query is invalid."""
