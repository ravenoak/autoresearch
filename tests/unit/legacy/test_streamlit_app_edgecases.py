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
    st.session_state['dark_mode'] = True
    monkeypatch.setattr(streamlit_app, 'st', st)
    streamlit_app.apply_theme_settings()
    st.session_state['dark_mode'] = False
    streamlit_app.apply_theme_settings()


def test_save_config_to_toml_error(tmp_path, monkeypatch):
    st = DummySt()
    monkeypatch.setattr(streamlit_app, 'st', st)
    monkeypatch.setattr('autoresearch.config_utils.st', st)
    monkeypatch.setattr(Path, 'cwd', lambda: tmp_path)

    def boom(*a, **k):
        raise OSError('fail')
    monkeypatch.setattr('tomli_w.dump', boom)
    assert streamlit_app.save_config_to_toml({'core': 'x'}) is False
