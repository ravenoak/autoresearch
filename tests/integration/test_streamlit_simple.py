# mypy: ignore-errors
from pathlib import Path

import pytest

from tests.optional_imports import import_or_skip

AppTest = import_or_skip("streamlit.testing.v1", attr="AppTest")

pytestmark = [pytest.mark.slow, pytest.mark.requires_ui]

# Use wrapper script to avoid path issues
APP_FILE = str(Path(__file__).resolve().with_name("streamlit_app_wrapper.py"))


@pytest.mark.integration
def test_streamlit_page_runs() -> None:
    """Test that the Streamlit app runs without hanging and renders content."""
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.session_state["_test_mode"] = True  # Disable background threads in tests
    at.run()
    # Check that markdown content was rendered (page loaded successfully)
    bodies = [m.proto.body for m in at.markdown]
    assert len(bodies) > 0, "No markdown content rendered"
    # Check for the main heading
    assert any("Autoresearch" in b for b in bodies), "Main heading not found"
