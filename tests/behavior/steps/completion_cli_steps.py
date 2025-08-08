from pytest_bdd import scenario, when, then

from autoresearch.main import app as cli_app
from .common_steps import assert_cli_success


@when("I run `autoresearch completion bash`")
def run_completion(cli_runner, bdd_context, isolate_network, restore_environment):
    result = cli_runner.invoke(cli_app, ["completion", "bash"])
    bdd_context["result"] = result


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    result = bdd_context["result"]
    assert_cli_success(result)
    assert "complete" in result.stdout.lower()


@scenario("../features/completion_cli.feature", "Generate shell completion script")
def test_completion_script():
    pass
