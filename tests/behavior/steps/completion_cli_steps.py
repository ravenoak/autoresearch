from pytest_bdd import scenario, when, then

from autoresearch.main import app as cli_app


@when("I run `autoresearch completion bash`")
def run_completion(cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["completion", "bash"])
    bdd_context["result"] = result


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert "complete" in result.stdout.lower()


@scenario("../features/completion_cli.feature", "Generate shell completion script")
def test_completion_script():
    pass
