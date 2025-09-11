"""Tests for the NLP optional extra."""

from __future__ import annotations

import pytest

from autoresearch.search.context import _try_import_spacy


@pytest.mark.requires_nlp
def test_spacy_available() -> None:
    """The NLP extra provides spaCy for search context features."""
    available = _try_import_spacy()
    if not available:
        pytest.skip("spaCy not available")
    assert available is True
