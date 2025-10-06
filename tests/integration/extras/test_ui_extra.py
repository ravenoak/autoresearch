# mypy: ignore-errors
"""Tests for the UI optional extra."""

from __future__ import annotations

import pytest

from autoresearch.streamlit_ui import apply_theme_settings


@pytest.mark.requires_ui
def test_streamlit_ui_helpers() -> None:
    """The UI extra exposes Streamlit helpers."""
    assert callable(apply_theme_settings)
