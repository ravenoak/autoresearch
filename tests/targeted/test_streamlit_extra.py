import types

from autoresearch import streamlit_app  # noqa: E402


def test_apply_accessibility(monkeypatch):
    calls = []
    fake_st = types.SimpleNamespace(markdown=lambda *a, **k: calls.append(a))
    fake_st.session_state = {'high_contrast': True}
    monkeypatch.setattr(streamlit_app, 'st', fake_st)
    streamlit_app.apply_accessibility_settings()
    assert len(calls) == 2
