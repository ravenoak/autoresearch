"""Ensure algorithm documentation references in search module stay valid.

The ranking components rely on BM25, semantic similarity and source
credibility heuristics. Their implementations reference algorithm docs; this
test asserts those paths exist to avoid stale links.
"""

from __future__ import annotations

from pathlib import Path

from autoresearch.search import core


DOC_PATHS = {
    "bm25": "docs/algorithms/bm25.md",
    "semantic": "docs/algorithms/semantic_similarity.md",
    "credibility": "docs/algorithms/source_credibility.md",
}


def repo_root() -> Path:
    """Return the repository root path."""

    return Path(__file__).resolve().parents[2]


def test_algorithm_docs_exist() -> None:
    """Algorithm documentation files referenced in docstrings must exist."""

    root = repo_root()
    for rel_path in DOC_PATHS.values():
        assert (root / rel_path).is_file(), f"Missing documentation: {rel_path}"


def test_core_docstrings_reference_docs() -> None:
    """Core search functions should mention their algorithm docs."""

    assert DOC_PATHS["bm25"] in (
        core.Search.calculate_bm25_scores.__doc__ or ""
    )
    assert DOC_PATHS["credibility"] in (
        core.Search.assess_source_credibility.__doc__ or ""
    )
    module_doc = core.__doc__ or ""
    for rel_path in DOC_PATHS.values():
        assert rel_path in module_doc
