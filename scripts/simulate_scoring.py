#!/usr/bin/env python
"""Simulate BM25, semantic similarity, and source credibility weighting.

Usage:
    uv run scripts/simulate_scoring.py --query "example"
"""

from __future__ import annotations

import argparse
from typing import List, TypedDict

from rank_bm25 import BM25Okapi


class Doc(TypedDict):
    id: int
    text: str
    credibility: float


SAMPLE_DOCS: List[Doc] = [
    {
        "id": 1,
        "text": "Python is a programming language that lets you work quickly",
        "credibility": 0.9,
    },
    {
        "id": 2,
        "text": "Snakes are legless reptiles known for their flexibility",
        "credibility": 0.6,
    },
    {
        "id": 3,
        "text": "Monty Python was a British surreal comedy group",
        "credibility": 0.8,
    },
]

WEIGHTS = (0.4, 0.4, 0.2)  # semantic, bm25, credibility


def tokenize(text: str) -> List[str]:
    """Return lowercase tokens."""
    return text.lower().split()


def cosine_similarity(vec1: List[int], vec2: List[int]) -> float:
    """Compute cosine similarity between integer vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    return dot / norm1 / norm2 if norm1 and norm2 else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate scoring heuristics")
    parser.add_argument("--query", required=True, help="Search query")
    args = parser.parse_args()

    corpus = [tokenize(d["text"]) for d in SAMPLE_DOCS]
    bm25 = BM25Okapi(corpus)
    bm25_scores = bm25.get_scores(tokenize(args.query))
    bm25_max = max(bm25_scores) or 1
    bm25_norm = [s / bm25_max for s in bm25_scores]

    vocab = sorted({w for doc in corpus for w in doc})
    vectors: List[List[int]] = []
    for toks in corpus:
        vectors.append([toks.count(t) for t in vocab])
    query_tokens = tokenize(args.query)
    query_vec = [query_tokens.count(t) for t in vocab]
    semantic_scores = [cosine_similarity(v, query_vec) for v in vectors]
    sem_max = max(semantic_scores) or 1
    sem_norm = [s / sem_max for s in semantic_scores]

    results: List[tuple[int, float, float, float, float]] = []
    for doc, bm, sem in zip(SAMPLE_DOCS, bm25_norm, sem_norm):
        final = WEIGHTS[0] * sem + WEIGHTS[1] * bm + WEIGHTS[2] * doc["credibility"]
        results.append((doc["id"], final, bm, sem, doc["credibility"]))

    results.sort(key=lambda r: r[1], reverse=True)
    for doc_id, final, bm, sem, cred in results:
        print(
            f"id={doc_id} final={final:.2f} bm25={bm:.2f} "
            f"semantic={sem:.2f} credibility={cred:.2f}"
        )


if __name__ == "__main__":
    main()
