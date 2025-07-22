import os
import pytest

pytestmark = pytest.mark.slow

AppTest = pytest.importorskip("streamlit.testing.v1", reason="streamlit testing module not available").AppTest

APP_FILE = os.path.join("src", "autoresearch", "streamlit_app.py")


def test_skip_link_has_aria_label():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.run()
    bodies = [m.proto.body for m in at.markdown]
    assert any("aria-label='Skip to main content'" in b or "aria-label=\"Skip to main content\"" in b for b in bodies)


def test_guided_tour_dialog_role():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = True
    at.run()
    bodies = [m.proto.body for m in at.markdown]
    assert any("role=\"dialog\"" in b for b in bodies)


def test_main_content_live_region():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.run()
    bodies = [m.proto.body for m in at.markdown]
    assert any("aria-live='polite'" in b or "aria-live=\"polite\"" in b for b in bodies)


def test_dark_mode_injects_styles():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.session_state["dark_mode"] = True
    at.run()
    styles = [m.proto.body for m in at.markdown if "<style>" in m.proto.body]
    assert any("background-color:#222" in css for css in styles)


def test_high_contrast_injects_styles():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.session_state["high_contrast"] = True
    at.run()
    styles = [m.proto.body for m in at.markdown if "<style>" in m.proto.body]
    assert any("background-color:#000" in css for css in styles)
