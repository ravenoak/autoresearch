import sys
from types import ModuleType, SimpleNamespace
import types

# Provide fake streamlit and matplotlib modules
fake_st = ModuleType("streamlit")
fake_st.markdown = lambda *a, **k: None
fake_st.set_page_config = lambda *a, **k: None
fake_st.session_state = {}
sys.modules.setdefault("streamlit", fake_st)
fake_matplotlib = ModuleType("matplotlib")
fake_matplotlib.use = lambda *a, **k: None
sys.modules.setdefault("matplotlib", fake_matplotlib)
sys.modules.setdefault("matplotlib.pyplot", ModuleType("pyplot"))

from autoresearch import streamlit_app


def test_apply_accessibility(monkeypatch):
    calls = []
    fake_st = types.SimpleNamespace(markdown=lambda *a, **k: calls.append(a))
    fake_st.session_state = {'high_contrast': True}
    monkeypatch.setattr(streamlit_app, 'st', fake_st)
    streamlit_app.apply_accessibility_settings()
    assert len(calls) == 2
