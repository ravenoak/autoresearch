from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenario, then, when
from typer.testing import CliRunner

from autoresearch.main import app as cli_app
from tests.behavior.steps import BehaviorContext, get_cli_result, set_cli_result


@when('I run `autoresearch visualize-metrics metrics.json metrics.png`')
def run_visualize_metrics(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    temp_config: Path,
    isolate_network: None,
) -> None:
    """Attempt to run the visualize-metrics command before it is implemented."""

    _ = temp_config
    result = cli_runner.invoke(
        cli_app,
        ["visualize-metrics", "metrics.json", "metrics.png"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@then('the CLI should report the command is missing')
def cli_reports_missing(bdd_context: BehaviorContext) -> None:
    """Ensure the CLI returns an error for the missing command."""

    result = get_cli_result(bdd_context)
    assert result.exit_code != 0
    assert "No such command" in result.output


@scenario('../features/visualize_metrics_cli.feature', 'Attempt to visualize metrics before implementation')
def test_visualize_metrics_cli() -> None:
    """Scenario: attempt to visualize metrics before implementation."""

