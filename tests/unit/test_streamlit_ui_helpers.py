from unittest.mock import MagicMock

import pytest
import streamlit as st

from autoresearch.streamlit_ui import apply_theme_settings


def test_apply_theme_settings_dark(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_markdown = MagicMock()

    monkeypatch.setattr(st, "markdown", mock_markdown)
    st.session_state["dark_mode"] = True
    apply_theme_settings()
    assert mock_markdown.called
