from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, List, Sequence


def _parse_timestamp(ts: Any) -> datetime:
    """Parse timestamps that may be ISO strings or ``datetime`` objects."""
    if isinstance(ts, datetime):
        dt = ts
    elif isinstance(ts, str):
        dt = datetime.fromisoformat(ts)
    else:
        dt = datetime.fromtimestamp(0, UTC)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _normalize(values: Sequence[float]) -> List[float]:
    """Normalize a sequence of numbers into the 0-1 range."""
    if not values:
        return []
    v_min = min(values)
    v_max = max(values)
    if v_max == v_min:
        return [0.0 for _ in values]
    return [(v - v_min) / (v_max - v_min) for v in values]


def rank_by_recency_and_relevance(
    results: Iterable[dict[str, Any]],
    *,
    relevance_key: str = "relevance",
    timestamp_key: str = "timestamp",
    recency_weight: float = 0.5,
) -> List[dict[str, Any]]:
    """Rank results by combining relevance and recency scores.

    Args:
        results: Iterable of search result dictionaries.
        relevance_key: Key containing the relevance score in each result.
        timestamp_key: Key containing ISO-formatted or ``datetime`` timestamps.
        recency_weight: Weight applied to the recency component. ``0`` means
            only relevance matters while ``1`` gives full preference to
            recency.

    Returns:
        List[dict[str, Any]]: Results ordered from best to worst.
    """
    now = datetime.now(UTC)
    processed: List[tuple[int, float, float, dict[str, Any]]] = []
    for idx, res in enumerate(results):
        relevance = float(res.get(relevance_key, 0.0))
        ts = _parse_timestamp(res.get(timestamp_key))
        age = (now - ts).total_seconds()
        processed.append((idx, relevance, age, res))

    if not processed:
        return []

    rel_norm = _normalize([p[1] for p in processed])
    age_norm = _normalize([p[2] for p in processed])
    scores: List[tuple[float, int, dict[str, Any]]] = []
    for (idx, _rel, _age, res), rn, an in zip(processed, rel_norm, age_norm):
        recency_score = 1 - an
        score = rn * (1 - recency_weight) + recency_score * recency_weight
        scores.append((score, idx, res))

    scores.sort(key=lambda s: (-s[0], s[1]))
    return [res for _, _, res in scores]
