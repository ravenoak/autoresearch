from pytest_bdd import scenarios

pytest_plugins = [
    "tests.behavior.steps.streamlit_gui_steps",
    "tests.behavior.steps.reasoning_modes_steps",
]

scenarios("../features/reasoning_mode_ui.feature")
