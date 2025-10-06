# mypy: ignore-errors
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import scenario, then, when
from typer.testing import CliRunner

from autoresearch.main import app as cli_app
from autoresearch.orchestration.orchestrator import Orchestrator
from tests.behavior.steps import BehaviorContext, get_cli_result, set_cli_result

pytest_plugins = ["tests.behavior.steps.common_steps"]


@when(
    'I run `autoresearch search "What is artificial intelligence?" --reasoning-mode direct`'
)
def run_search_direct(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    dummy_query_response: Any,
    temp_config: Path,
    isolate_network: None,
) -> None:
    """Execute the search command using the direct reasoning mode."""

    _ = temp_config
    monkeypatch.setattr(Orchestrator, "run_query", lambda *_a, **_k: dummy_query_response)
    result = cli_runner.invoke(
        cli_app,
        ["search", "What is artificial intelligence?", "--reasoning-mode", "direct"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@when('I run `autoresearch search`')
def run_search_missing(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    temp_config: Path,
    isolate_network: None,
) -> None:
    """Invoke the search command without required arguments."""

    _ = temp_config
    result = cli_runner.invoke(cli_app, ["search"], catch_exceptions=False)
    set_cli_result(bdd_context, result)


@then('the CLI should exit successfully')
def cli_success(bdd_context: BehaviorContext) -> None:
    """Assert the search command succeeded."""

    result = get_cli_result(bdd_context)
    assert result.exit_code == 0
    assert result.stderr == ""


@then('the CLI should exit with an error')
def cli_error(bdd_context: BehaviorContext) -> None:
    """Assert the search command failed with an informative error."""

    result = get_cli_result(bdd_context)
    assert result.exit_code != 0
    assert result.stderr != "" or result.exception is not None


@scenario('../features/search_cli.feature', 'Run a basic search query')
def test_search_direct() -> None:
    """Scenario: Run a basic search query."""


@scenario('../features/search_cli.feature', 'Missing query argument')
def test_search_missing() -> None:
    """Scenario: Missing query argument produces an error."""
