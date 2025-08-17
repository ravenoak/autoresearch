"""Stub for :mod:`streamlit` to avoid heavy UI dependency."""

import sys
import types

if "streamlit" not in sys.modules:
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
    st_stub.metric = lambda *a, **k: None
    st_stub.sidebar = types.SimpleNamespace(metric=lambda *a, **k: None)
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
    sys.modules["streamlit"] = st_stub
