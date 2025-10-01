from typing import Any
from unittest.mock import MagicMock

import pytest
import streamlit as st

from autoresearch.streamlit_ui import apply_theme_settings


def test_apply_theme_settings_dark(monkeypatch: pytest.MonkeyPatch) -> None:
    m = MagicMock()
    def apply_markdown(*_args: Any, **_kwargs: Any) -> None:
        m(*_args, **_kwargs)

    monkeypatch.setattr(st, "markdown", apply_markdown)
    st.session_state["dark_mode"] = True
    apply_theme_settings()
    assert m.called
