"""Simulation for convergence of search ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .ranking import normalize_scores
from .ranking_formula import validate_weights


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


def relevance_scores(docs: Iterable[DocScores], weights: Sequence[float]) -> List[float]:
    """Compute relevance scores from component scores.

    Args:
        docs: Iterable of :class:`DocScores`.
        weights: Tuple of BM25, semantic, and credibility weights.

    Returns:
        List[float]: Weighted relevance scores.
    """
    validate_weights(weights)
    doc_list = list(docs)
    w_bm25, w_sem, w_cred = weights
    bm25_norm = normalize_scores([d.bm25 for d in doc_list])
    sem_norm = normalize_scores([d.semantic for d in doc_list])
    cred_norm = normalize_scores([d.credibility for d in doc_list])
    combined = [
        bm25_norm[i] * w_bm25 + sem_norm[i] * w_sem + cred_norm[i] * w_cred
        for i in range(len(doc_list))
    ]
    return normalize_scores(combined)


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
