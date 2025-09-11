"""Stub for :mod:`streamlit` to avoid heavy UI dependency."""

import importlib.util
import sys
import types

if importlib.util.find_spec("streamlit") is None and "streamlit" not in sys.modules:
    st_stub = types.ModuleType("streamlit")
    st_stub.markdown = lambda *a, **k: None

    class SessionState(dict):
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__

    st_stub.session_state = SessionState()
    st_stub.set_page_config = lambda *a, **k: None
    st_stub.text_area = lambda *a, **k: ""
    st_stub.selectbox = lambda *a, **k: None
    st_stub.slider = lambda *a, **k: 0
    st_stub.button = lambda *a, **k: False
    st_stub.columns = lambda *a, **k: (
        types.SimpleNamespace(),
        types.SimpleNamespace(),
    )
    st_stub.container = lambda: types.SimpleNamespace(
        __enter__=lambda s: None,
        __exit__=lambda s, e, t, b: None,
    )
    st_stub.modal = lambda *a, **k: types.SimpleNamespace(
        __enter__=lambda s: None,
        __exit__=lambda s, e, t, b: None,
    )
    st_stub.__version__ = "0.0"
    st_stub.__spec__ = importlib.util.spec_from_loader("streamlit", loader=None)
    sys.modules["streamlit"] = st_stub
