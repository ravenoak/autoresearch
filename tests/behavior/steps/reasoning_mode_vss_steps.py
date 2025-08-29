from pytest_bdd import scenarios

pytest_plugins = [
    "tests.behavior.steps.vector_extension_handling_steps",
    "tests.behavior.steps.reasoning_mode_steps",
    "tests.behavior.steps.agent_orchestration_steps",
]

scenarios("../features/reasoning_mode_vss.feature")
