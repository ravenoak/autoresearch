from __future__ import annotations

import sys
import types

import pytest
from pytest_bdd import given, scenarios, when
from typer.testing import CliRunner

from autoresearch.main import app as cli_app
from tests.behavior.steps import BehaviorContext, set_cli_result


@given("the capabilities command environment is prepared")
def capabilities_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub optional dependencies so the CLI command can execute."""

    monkeypatch.setitem(sys.modules, "docx", types.SimpleNamespace(Document=object))
    monkeypatch.setitem(
        sys.modules,
        "autoresearch.main.llm",
        types.SimpleNamespace(get_available_adapters=lambda: {}),
    )
    from autoresearch.orchestration import ReasoningMode

    monkeypatch.setitem(
        sys.modules,
        "autoresearch.main.orchestration",
        types.SimpleNamespace(ReasoningMode=ReasoningMode),
    )


@when("I run the capabilities command")
def run_capabilities(cli_runner: CliRunner, bdd_context: BehaviorContext) -> None:
    """Invoke the CLI to print available capabilities."""

    result = cli_runner.invoke(cli_app, ["capabilities"])
    set_cli_result(bdd_context, result)


scenarios("../features/capabilities_cli.feature")

