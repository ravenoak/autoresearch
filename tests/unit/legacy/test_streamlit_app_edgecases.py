# mypy: ignore-errors
import types
from pathlib import Path

from autoresearch import streamlit_app


class DummySt(types.SimpleNamespace):
    def __init__(self):
        super().__init__(markdown=lambda *a, **k: None, error=lambda *a, **k: None)
        self.session_state = {}


def test_apply_theme_settings(monkeypatch):
    st = DummySt()
    st.session_state["dark_mode"] = True
    monkeypatch.setattr(streamlit_app, "st", st)
    streamlit_app.apply_theme_settings()
    st.session_state["dark_mode"] = False
    streamlit_app.apply_theme_settings()


def test_save_config_to_toml_error(tmp_path, monkeypatch):
    st = DummySt()
    monkeypatch.setattr(streamlit_app, "st", st)
    # Patch the lazy-loaded streamlit instance in config_utils
    from autoresearch import config_utils

    monkeypatch.setattr(config_utils, "_st", None)  # Reset the cached streamlit instance
    monkeypatch.setattr(config_utils, "_streamlit_available", None)  # Reset availability flag

    def mock_get_streamlit():
        return st

    monkeypatch.setattr(config_utils, "_get_streamlit", mock_get_streamlit)
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    def boom(*a, **k):
        raise OSError("fail")

    monkeypatch.setattr("tomli_w.dump", boom)
    assert streamlit_app.save_config_to_toml({"core": "x"}) is False
