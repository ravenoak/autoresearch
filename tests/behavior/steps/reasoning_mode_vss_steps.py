from pytest_bdd import scenario

pytest_plugins = [
    "tests.behavior.steps.vector_extension_handling_steps",
    "tests.behavior.steps.reasoning_mode_steps",
    "tests.behavior.steps.agent_orchestration_steps",
]


@scenario(
    "../features/reasoning_mode_vss.feature",
    "Dialectical reasoning uses VSS extension",
)
def test_reasoning_mode_vss() -> None:
    """Ensure reasoning modes work with the VSS extension."""
