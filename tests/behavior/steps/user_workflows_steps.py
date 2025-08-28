from pytest_bdd import scenario

pytest_plugins = [
    "tests.behavior.steps.common_steps",
    "tests.behavior.steps.streamlit_gui_steps",
]


@scenario("../features/user_workflows.feature", "CLI search completes successfully")
def test_cli_workflow(bdd_context):
    assert bdd_context["result"].exit_code == 0


@scenario(
    "../features/user_workflows.feature",
    "CLI search with invalid backend reports error",
)
def test_cli_workflow_invalid_backend(bdd_context):
    assert bdd_context["result"].exit_code != 0


@scenario(
    "../features/user_workflows.feature",
    "Streamlit interface displays results",
)
def test_streamlit_ui_workflow() -> None:
    """Ensure the Streamlit UI renders search results."""
