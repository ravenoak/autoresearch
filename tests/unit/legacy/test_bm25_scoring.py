# mypy: ignore-errors
"""Regression tests for BM25 scoring implementation."""

from typing import Any, Dict, List
import pytest
from rank_bm25 import BM25Okapi

try:
    import docx  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    import tests.stubs.docx  # noqa: F401

from autoresearch.search import Search


def test_calculate_bm25_scores_real_documents() -> None:
    """Calculate BM25 scores using the real library and verify normalization."""
    docs: List[Dict[str, Any]] = [
        {"title": "Python scripting", "snippet": "Python is great for scripting."},
        {"title": "Java docs", "snippet": "This document talks about Java."},
        {
            "title": "Programming languages",
            "snippet": "Python and Java both are programming languages.",
        },
    ]
    query = "python"

    scores = Search.calculate_bm25_scores(query=query, documents=docs)

    query_tokens = Search.preprocess_text(query)
    corpus = [Search.preprocess_text(d["title"] + " " + d.get("snippet", "")) for d in docs]
    bm25 = BM25Okapi(corpus)
    expected = bm25.get_scores(query_tokens)
    expected = expected / expected.max()

    assert scores == pytest.approx(expected.tolist())
