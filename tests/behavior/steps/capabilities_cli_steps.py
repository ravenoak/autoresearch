from pytest_bdd import scenario, when, then

from autoresearch.main import app as cli_app


@when("I run `autoresearch capabilities`")
def run_capabilities(cli_runner, bdd_context, monkeypatch):
    import sys
    import types

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
    result = cli_runner.invoke(cli_app, ["capabilities"])
    bdd_context["result"] = result


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert "capabilities" in result.stdout.lower()
    assert result.stderr == ""


@scenario("../features/capabilities_cli.feature", "List available capabilities")
def test_capabilities_cmd():
    pass
