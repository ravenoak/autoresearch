from pytest_bdd import scenario, when, then

from autoresearch.main import app as cli_app


@when("I run `autoresearch serve --help`")
def run_serve_help(cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["serve", "--help"])
    bdd_context["result"] = result


@when("I run `autoresearch serve-a2a --help`")
def run_a2a_help(cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["serve-a2a", "--help"])
    bdd_context["result"] = result


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    assert bdd_context["result"].exit_code == 0


@scenario("../features/serve_commands.feature", "Display help for serve")
def test_serve_help():
    pass


@scenario("../features/serve_commands.feature", "Display help for serve-a2a")
def test_serve_a2a_help():
    pass
