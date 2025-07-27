from pytest_bdd import scenario, when, then

from autoresearch.main import app as cli_app


@when("I run `autoresearch capabilities`")
def run_capabilities(cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["capabilities"])
    bdd_context["result"] = result


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    assert bdd_context["result"].exit_code == 0


@scenario("../features/capabilities_cli.feature", "List available capabilities")
def test_capabilities_cmd():
    pass
