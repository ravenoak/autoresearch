# mypy: ignore-errors
from __future__ import annotations

from pathlib import Path
from typing import Protocol, cast

import pytest
from pytest_bdd import then, when
from typer.testing import CliRunner

from autoresearch.main import app as cli_app
from tests.behavior.steps import BehaviorContext, get_cli_result, set_cli_result


class VisualizationHooks(Protocol):
    def visualize_query(self, query: str, output: str, layout: str = ...) -> None: ...

    def visualize(self, *args: object, **kwargs: object) -> None: ...


class VisualizationApp(Protocol):
    visualization_hooks: VisualizationHooks


CLI_APP_WITH_HOOKS = cast(VisualizationApp, cli_app)


@when('I run `autoresearch visualize "What is quantum computing?" graph.png`')
def run_visualize_query(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    temp_config: Path,
) -> None:
    # Run the actual CLI command
    result = cli_runner.invoke(
        cli_app,
        ["visualize", "What is quantum computing?", "graph.png"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@when("I run `autoresearch visualize-rdf rdf_graph.png`")
def run_visualize_rdf(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    temp_config: Path,
) -> None:
    monkeypatch.setattr(CLI_APP_WITH_HOOKS.visualization_hooks, "visualize", lambda *a, **k: None)
    result = cli_runner.invoke(cli_app, ["visualize-rdf", "rdf_graph.png"], catch_exceptions=False)
    set_cli_result(bdd_context, result)


@when('I run `autoresearch visualize "What is quantum computing?"`')
def run_visualize_missing(
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    temp_config: Path,
) -> None:
    def _raise(*_: object, **__: object) -> None:
        raise RuntimeError("missing output")

    monkeypatch.setattr(CLI_APP_WITH_HOOKS.visualization_hooks, "visualize_query", _raise)
    result = cli_runner.invoke(
        cli_app,
        ["visualize", "What is quantum computing?"],
        catch_exceptions=False,
    )
    set_cli_result(bdd_context, result)


@then("the CLI should exit successfully")
def cli_success(bdd_context: BehaviorContext) -> None:
    result = get_cli_result(bdd_context)
    assert result.exit_code == 0
    # Allow structured logs in stderr - success is determined by exit code and file creation


@then("the CLI should exit with an error")
def cli_error(bdd_context: BehaviorContext) -> None:
    result = get_cli_result(bdd_context)
    assert result.exit_code != 0
    assert result.stderr != "" or result.exception is not None


@then('the file "graph.png" should be created')
def check_graph_created() -> None:
    assert Path("graph.png").exists()
