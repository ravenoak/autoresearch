from unittest.mock import MagicMock

import streamlit as st

from autoresearch.streamlit_ui import apply_theme_settings
import pytest


def test_apply_theme_settings_dark(monkeypatch: pytest.MonkeyPatch) -> None:
    m = MagicMock()
    monkeypatch.setattr(st, "markdown", m)
    st.session_state["dark_mode"] = True
    apply_theme_settings()
    assert m.called
