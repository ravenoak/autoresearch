"""Utilities for combining search ranking scores.

This module implements the convex ranking strategy used across Autoresearch.
Each component score is first normalized to the 0–1 range before weights are
applied. The weighted sum is then normalized again to keep the final relevance
scores bounded and comparable across backends.
"""

from __future__ import annotations

import math
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

    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        return [0.0 for _ in scores]

    scale = max_score - min_score
    return [(s - min_score) / scale for s in scores]


def validate_weights(weights: Sequence[float]) -> None:
    """Ensure ranking weights form a convex combination.

    Args:
        weights: Sequence of component weights in BM25, semantic, credibility
            order.

    Raises:
        ValueError: If weights are negative, do not sum to 1.0, or do not have
            exactly three components.
    """

    if len(weights) != 3:
        raise ValueError("weights must have three components")
    if any(w < 0 for w in weights):
        raise ValueError("weights must be non-negative")
    if not math.isclose(sum(weights), 1.0, abs_tol=1e-3):
        raise ValueError("weights must sum to 1.0")


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
        weights: Tuple of weights ``(bm25, semantic, credibility)``. The values
            must form a convex combination.

    Returns:
        List[float]: Final normalized relevance scores.

    Raises:
        ValueError: If score lengths differ or weights are invalid.
    """
    if not (len(bm25) == len(semantic) == len(credibility)):
        raise ValueError("Score sequences must have equal length")

    validate_weights(weights)

    bm25_norm = normalize_scores(bm25)
    semantic_norm = normalize_scores(semantic)
    credibility_norm = normalize_scores(credibility)

    combined = [
        (
            bm25_norm[i] * weights[0]
            + semantic_norm[i] * weights[1]
            + credibility_norm[i] * weights[2]
        )
        for i in range(len(bm25_norm))
    ]
    return normalize_scores(combined)
