"""Simulation for convergence of search ranking."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class DocScores:
    """Component scores used during ranking.

    Args:
        bm25: Lexical match score.
        semantic: Embedding similarity score.
        credibility: Domain credibility score.
    """

    bm25: float
    semantic: float
    credibility: float


def _validate_weights(weights: Sequence[float]) -> None:
    """Ensure ranking weights sum to 1.0."""
    if not math.isclose(sum(weights), 1.0, abs_tol=1e-9):
        raise ValueError("weights must sum to 1.0")


def _normalize(values: Sequence[float]) -> List[float]:
    """Scale values to the 0–1 range."""
    max_val = max(values, default=0.0)
    if max_val <= 0:
        return [0.0 for _ in values]
    return [v / max_val for v in values]


def relevance_scores(docs: Iterable[DocScores], weights: Sequence[float]) -> List[float]:
    """Compute relevance scores from component scores.

    Args:
        docs: Iterable of :class:`DocScores`.
        weights: Tuple of BM25, semantic, and credibility weights.

    Returns:
        List[float]: Weighted relevance scores.
    """
    _validate_weights(weights)
    doc_list = list(docs)
    w_bm25, w_sem, w_cred = weights
    bm25_norm = _normalize([d.bm25 for d in doc_list])
    sem_norm = _normalize([d.semantic for d in doc_list])
    cred_norm = _normalize([d.credibility for d in doc_list])
    combined = [
        bm25_norm[i] * w_bm25 + sem_norm[i] * w_sem + cred_norm[i] * w_cred
        for i in range(len(doc_list))
    ]
    final_max = max(combined) or 1.0
    return [score / final_max for score in combined]


def simulate_ranking_convergence(
    docs: Sequence[DocScores],
    weights: Sequence[float],
    iterations: int = 3,
) -> List[List[int]]:
    """Rank documents repeatedly to illustrate convergence.

    Args:
        docs: Sequence of documents with component scores.
        weights: Ranking weights that must sum to 1.0.
        iterations: Number of ranking rounds to perform.

    Returns:
        List[List[int]]: Index orderings for each iteration.
    """
    orderings: List[List[int]] = []
    current_docs = list(docs)
    indices = list(range(len(docs)))
    for _ in range(iterations):
        scores = relevance_scores(current_docs, weights)
        ordering = sorted(range(len(current_docs)), key=lambda i: scores[i], reverse=True)
        orderings.append([indices[i] for i in ordering])
        current_docs = [current_docs[i] for i in ordering]
        indices = [indices[i] for i in ordering]
    return orderings
