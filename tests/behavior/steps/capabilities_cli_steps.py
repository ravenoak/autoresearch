from tests.behavior.context import BehaviorContext
import sys
import types

from pytest_bdd import given, when, scenarios
from autoresearch.main import app as cli_app


@given("the capabilities command environment is prepared")
def capabilities_env(monkeypatch):
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
def run_capabilities(cli_runner, bdd_context: BehaviorContext):
    result = cli_runner.invoke(cli_app, ["capabilities"])
    bdd_context["result"] = result


scenarios("../features/capabilities_cli.feature")
