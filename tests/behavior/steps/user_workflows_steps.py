from pytest_bdd import scenario

pytest_plugins = ["tests.behavior.steps.common_steps"]


@scenario("../features/user_workflows.feature", "CLI search completes successfully")
def test_cli_workflow(bdd_context):
    assert bdd_context["result"].exit_code == 0
