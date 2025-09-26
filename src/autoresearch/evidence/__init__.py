"""Utilities for evidence retrieval expansion and entailment scoring."""

import re
from dataclasses import dataclass
from typing import Iterable, List

from ..storage import ClaimAuditStatus

_STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "and",
    "in",
    "to",
    "for",
    "on",
    "at",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "with",
    "from",
    "that",
    "this",
}

_NEGATION_TERMS = {"no", "not", "never", "without", "none", "neither"}


@dataclass(frozen=True)
class EntailmentBreakdown:
    """Structured insight returned by :func:`score_entailment`."""

    score: float
    overlap_ratio: float
    support_ratio: float
    overlapping_terms: List[str]


def expand_retrieval_queries(
    claim: str,
    *,
    base_query: str | None = None,
    max_variations: int = 5,
) -> List[str]:
    """Generate lightweight retrieval queries for a claim."""

    cleaned = claim.strip()
    if not cleaned:
        return []

    variations: list[str] = []
    seen: set[str] = set()
    candidates = [cleaned]
    if base_query:
        candidates.append(f"{base_query.strip()} {cleaned}")

    keywords = _extract_keywords(cleaned)
    if keywords:
        candidates.append(" ".join(keywords))

    candidates.extend(
        [
            f"evidence supporting {cleaned}",
            f"evidence contradicting {cleaned}",
        ]
    )

    for candidate in candidates:
        normalised = " ".join(candidate.split())
        key = normalised.lower()
        if normalised and key not in seen:
            variations.append(normalised)
            seen.add(key)
        if len(variations) >= max_variations:
            break

    return variations


def score_entailment(claim: str, evidence: str) -> EntailmentBreakdown:
    """Return a lightweight lexical entailment estimate."""

    claim_tokens = _tokenize(claim)
    evidence_tokens = _tokenize(evidence)
    if not claim_tokens or not evidence_tokens:
        return EntailmentBreakdown(0.0, 0.0, 0.0, [])

    claim_counts = _frequency_vector(claim_tokens)
    evidence_counts = _frequency_vector(evidence_tokens)

    overlap = sum(min(claim_counts[token], evidence_counts.get(token, 0)) for token in claim_counts)
    overlap_ratio = overlap / max(sum(claim_counts.values()), 1)
    support_ratio = overlap / max(sum(evidence_counts.values()), 1)

    score = (overlap_ratio + support_ratio) / 2

    claim_negated = bool(_NEGATION_TERMS.intersection(claim_counts))
    evidence_negated = bool(_NEGATION_TERMS.intersection(evidence_counts))
    if claim_negated != evidence_negated and score > 0:
        score *= 0.6
    elif claim_negated and evidence_negated:
        score = min(1.0, score + 0.1)

    overlapping_terms = sorted({token for token in claim_counts if token in evidence_counts})
    score = max(0.0, min(1.0, score))

    return EntailmentBreakdown(score, overlap_ratio, support_ratio, overlapping_terms)


def classify_entailment(score: float) -> ClaimAuditStatus:
    """Map an entailment score to a :class:`ClaimAuditStatus`."""

    return ClaimAuditStatus.from_entailment(score)


def _tokenize(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9']+", text.lower()) if token not in _STOPWORDS]


def _frequency_vector(tokens: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def _extract_keywords(text: str) -> List[str]:
    tokens = _tokenize(text)
    return tokens[:8]


__all__ = [
    "EntailmentBreakdown",
    "classify_entailment",
    "expand_retrieval_queries",
    "score_entailment",
]
