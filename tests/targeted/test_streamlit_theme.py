import types
from autoresearch import streamlit_app


def test_apply_theme_settings(monkeypatch):
    calls = []
    fake_st = types.SimpleNamespace(markdown=lambda *a, **k: calls.append(a), session_state={"dark_mode": True})
    monkeypatch.setattr(streamlit_app, "st", fake_st)
    streamlit_app.apply_theme_settings()
    assert calls
    fake_st.session_state["dark_mode"] = False
    streamlit_app.apply_theme_settings()
    assert len(calls) > 1
