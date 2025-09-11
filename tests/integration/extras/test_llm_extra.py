"""Tests for the LLM optional extra."""

from __future__ import annotations

import pytest

from autoresearch.search.context import _try_import_sentence_transformers


@pytest.mark.requires_llm
def test_fastembed_available() -> None:
    """The LLM extra installs fast embedding models."""
    assert _try_import_sentence_transformers() is True
