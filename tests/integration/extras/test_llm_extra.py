"""Tests for the LLM optional extra."""

from __future__ import annotations

import pytest



@pytest.mark.requires_llm
def test_fastembed_available() -> None:
    """The LLM extra installs fast embedding models."""
    fastembed = pytest.importorskip("fastembed")
    assert hasattr(fastembed, "TextEmbedding")
