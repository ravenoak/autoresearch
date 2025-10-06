# mypy: ignore-errors
"""Tests for the LLM optional extra."""

from __future__ import annotations

import pytest

from tests.optional_imports import import_or_skip


@pytest.mark.requires_llm
def test_fastembed_available() -> None:
    """The LLM extra installs fast embedding models."""
    fastembed = import_or_skip("fastembed")
    assert any(
        hasattr(fastembed, attr) for attr in ("OnnxTextEmbedding", "TextEmbedding")
    )
