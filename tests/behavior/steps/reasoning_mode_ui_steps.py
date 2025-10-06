# mypy: ignore-errors
from pytest_bdd import scenarios
import pytest

pytest_plugins = [
    "tests.behavior.steps.streamlit_gui_steps",
    "tests.behavior.steps.reasoning_modes_steps",
]

pytestmark = pytest.mark.requires_ui

scenarios("../features/reasoning_mode_ui.feature")
