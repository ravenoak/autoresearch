"""Utilities for combining search ranking scores.

This module implements the weighted ranking strategy described in
``docs/specs/search_ranking.md``. Component scores are first normalized to
keep values in the 0–1 range. The final relevance score is a weighted sum of
BM25, semantic similarity, and source credibility, and is normalized again
before sorting results. This ensures stable ordering across backends.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple


def normalize_scores(scores: Sequence[float]) -> List[float]:
    """Scale a sequence of scores to the 0–1 interval.

    Args:
        scores: Raw scores from a ranking component.

    Returns:
        List[float]: Scores normalized between 0 and 1.
    """
    if not scores:
        return []
    max_score = max(scores)
    if max_score <= 0:
        return [0.0 for _ in scores]
    return [s / max_score for s in scores]


def combine_scores(
    bm25: Sequence[float],
    semantic: Sequence[float],
    credibility: Sequence[float],
    weights: Tuple[float, float, float],
) -> List[float]:
    """Merge ranking components using a weighted sum.

    Args:
        bm25: BM25 relevance scores.
        semantic: Semantic similarity scores.
        credibility: Source credibility or freshness scores.
        weights: Tuple of weights ``(bm25, semantic, credibility)`` that must
            sum to 1.0.

    Returns:
        List[float]: Final normalized relevance scores.

    Raises:
        ValueError: If score lengths differ or weights are invalid.
    """
    if not (len(bm25) == len(semantic) == len(credibility)):
        raise ValueError("Score sequences must have equal length")

    if abs(sum(weights) - 1.0) > 0.001:
        raise ValueError("Weights must sum to 1.0")
    if any(w < 0 for w in weights):
        raise ValueError("Weights must be non-negative")

    combined = [
        bm25[i] * weights[0]
        + semantic[i] * weights[1]
        + credibility[i] * weights[2]
        for i in range(len(bm25))
    ]
    return normalize_scores(combined)
