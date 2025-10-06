# mypy: ignore-errors
from __future__ import annotations

import typer
from typer.testing import CliRunner

from tests.behavior.context import (
    BehaviorContext,
    CLIInvocation,
    get_cli_invocation,
    get_cli_result,
    set_cli_invocation,
    set_cli_result,
)

app = typer.Typer()


@app.command()
def hello() -> None:
    """Simple command used for CLI helper tests."""

    typer.echo("hi")


def test_cli_helpers_store_and_retrieve_results() -> None:
    context: BehaviorContext = {}
    runner = CliRunner()
    result = runner.invoke(app, ["hello"])

    stored_result = set_cli_result(context, result)
    assert stored_result is result
    assert get_cli_result(context) is result

    invocation = set_cli_invocation(context, ["hello"], result)
    assert isinstance(invocation, CLIInvocation)
    assert invocation.command == ("hello",)
    assert invocation.result is result
    assert get_cli_invocation(context) is invocation

    # Compatibility path used by existing steps.
    set_cli_result(context, result, key="result")
    assert get_cli_result(context, key="result") is result
