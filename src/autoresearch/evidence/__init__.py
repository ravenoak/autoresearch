"""Utilities for evidence retrieval expansion and entailment scoring."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Iterable, List, Mapping, Sequence

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


@dataclass(frozen=True)
class EntailmentAggregate:
    """Summary statistics derived from multiple entailment checks."""

    mean: float
    variance: float
    sample_size: int
    disagreement: bool
    scores: List[float]


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


def sample_paraphrases(text: str, *, max_samples: int = 3) -> List[str]:
    """Return lightweight paraphrases for retrieval retries."""

    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return []

    variants: list[str] = []
    seen: set[str] = set()
    base = cleaned.rstrip("?.!")
    if not base:
        base = cleaned
    candidates = [cleaned, base, f"Is it true that {base}?", f"Summarise evidence for {base}"]
    if len(base.split()) > 3:
        candidates.append(f"Evidence for whether {base}")
        candidates.append(f"Counterexamples to {base}")

    for candidate in candidates:
        normalised = " ".join(candidate.split())
        key = normalised.lower()
        if normalised and key not in seen:
            variants.append(normalised)
            seen.add(key)
        if len(variants) >= max_samples:
            break

    return variants


def aggregate_entailment_scores(
    breakdowns: Sequence[EntailmentBreakdown | float],
    *,
    disagreement_threshold: float = 0.25,
    variance_threshold: float = 0.04,
) -> EntailmentAggregate:
    """Aggregate lexical entailment checks into stability diagnostics."""

    scores: list[float] = []
    for item in breakdowns:
        try:
            value = item.score if isinstance(item, EntailmentBreakdown) else float(item)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value):
            continue
        scores.append(max(0.0, min(1.0, value)))

    if not scores:
        return EntailmentAggregate(0.0, 0.0, 0, False, [])

    sample_size = len(scores)
    mean = sum(scores) / sample_size
    if sample_size > 1:
        variance = sum((score - mean) ** 2 for score in scores) / (sample_size - 1)
    else:
        variance = 0.0
    spread = max(scores) - min(scores)
    disagreement = (spread >= disagreement_threshold) or (variance >= variance_threshold)
    return EntailmentAggregate(mean, variance, sample_size, disagreement, scores)


def _tokenize(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9']+", text.lower()) if token not in _STOPWORDS]


def extract_candidate_claims(
    text: str,
    *,
    max_claims: int = 8,
    min_tokens: int = 5,
) -> List[str]:
    """Extract declarative claim candidates from ``text`` for reverification."""

    cleaned = text.strip()
    if not cleaned:
        return []

    claims: list[str] = []
    seen: set[str] = set()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    for line in lines or [cleaned]:
        normalised = re.sub(r"^([0-9]+[.)]|[-*•])\s+", "", line).strip()
        if not normalised:
            continue
        segments = re.split(r"(?<=[.!?])\s+", normalised) if " " in normalised else [normalised]
        for segment in segments:
            candidate = " ".join(segment.strip().split())
            if not candidate:
                continue
            if candidate.endswith("?"):
                continue
            if len(candidate.split()) < min_tokens:
                continue
            key = candidate.lower()
            if key in seen:
                continue
            seen.add(key)
            claims.append(candidate)
            if len(claims) >= max_claims:
                return claims
    return claims


def should_retry_verification(
    audits: Sequence[Mapping[str, Any]] | None,
    *,
    min_supported: int = 1,
    min_sample_size: int = 1,
) -> bool:
    """Return ``True`` when another verification pass should run."""

    if not audits:
        return True

    supported = 0
    total_samples = 0
    needs_review_only = True

    for audit in audits:
        status_token = audit.get("status")
        try:
            status = (
                status_token
                if isinstance(status_token, ClaimAuditStatus)
                else ClaimAuditStatus(str(status_token))
            )
        except ValueError:
            status = ClaimAuditStatus.NEEDS_REVIEW

        if status is ClaimAuditStatus.SUPPORTED:
            supported += 1
            needs_review_only = False
        elif status is ClaimAuditStatus.UNSUPPORTED:
            needs_review_only = False

        sample_size = audit.get("sample_size")
        try:
            total_samples += int(sample_size) if sample_size is not None else 0
        except (TypeError, ValueError):
            continue

    if supported >= min_supported:
        return False
    if total_samples >= min_sample_size and not needs_review_only:
        return False
    return True


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
    "EntailmentAggregate",
    "aggregate_entailment_scores",
    "classify_entailment",
    "extract_candidate_claims",
    "expand_retrieval_queries",
    "sample_paraphrases",
    "score_entailment",
    "should_retry_verification",
]
