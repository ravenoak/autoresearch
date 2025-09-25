import types
from unittest.mock import MagicMock

import pytest

from autoresearch import streamlit_ui

pytestmark = pytest.mark.requires_ui


class Session(dict):
    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value


def test_apply_accessibility_settings_no_high_contrast(monkeypatch):
    calls = []
    fake_st = types.SimpleNamespace(
        markdown=lambda *a, **k: calls.append(a),
        session_state=Session(),
    )
    monkeypatch.setattr(streamlit_ui, "st", fake_st)
    streamlit_ui.apply_accessibility_settings()
    assert len(calls) == 1


def test_apply_theme_settings_light(monkeypatch):
    m = MagicMock()
    fake_st = types.SimpleNamespace(markdown=m, session_state={"dark_mode": False})
    monkeypatch.setattr(streamlit_ui, "st", fake_st)
    streamlit_ui.apply_theme_settings()
    assert m.called and "background-color:#fff" in m.call_args[0][0]


class _DummyContext:
    def __init__(self):
        self.entered = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def test_display_guided_tour_dismiss(monkeypatch):
    ctx = _DummyContext()
    calls = {"modal": 0}
    def track_modal(*_args, **_kwargs):
        calls["modal"] += 1
        return ctx

    fake_st = types.SimpleNamespace(
        markdown=lambda *a, **k: None,
        modal=track_modal,
        button=lambda *a, **k: True,
        session_state=Session(),
    )
    monkeypatch.setattr(streamlit_ui, "st", fake_st)
    streamlit_ui.display_guided_tour()
    assert fake_st.session_state.show_tour is False
    assert calls["modal"] == 1 and ctx.entered


def test_display_help_sidebar_dismiss(monkeypatch):
    ctx = _DummyContext()
    sidebar = types.SimpleNamespace(expander=lambda *a, **k: ctx)
    fake_st = types.SimpleNamespace(
        markdown=lambda *a, **k: None,
        sidebar=sidebar,
        button=lambda *a, **k: True,
        session_state=Session(),
    )
    monkeypatch.setattr(streamlit_ui, "st", fake_st)
    streamlit_ui.display_help_sidebar()
    assert fake_st.session_state.first_visit is False
    assert ctx.entered
