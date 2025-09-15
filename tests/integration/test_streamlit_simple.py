import os

import pytest

from tests.optional_imports import import_or_skip

AppTest = import_or_skip("streamlit.testing.v1", attr="AppTest")

pytestmark = [pytest.mark.slow, pytest.mark.requires_ui]

APP_FILE = os.path.join("src", "autoresearch", "streamlit_app.py")


@pytest.mark.integration
def test_streamlit_page_runs():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.run()
    assert at.title
