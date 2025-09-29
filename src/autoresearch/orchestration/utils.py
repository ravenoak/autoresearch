from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Deque, TypeVar

from ..models import QueryResponse


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()
        return float(memory_info.rss) / (1024 * 1024)
    except ImportError:  # pragma: no cover - fallback path
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        return float(usage.ru_maxrss) / 1024


@dataclass(frozen=True)
class TokenUsageSnapshot:
    """Summary of token usage statistics emitted by orchestration metrics."""

    total: float
    max_tokens: float

    @property
    def utilization_ratio(self) -> float:
        """Return the utilisation ratio guarding against division by zero."""

        if self.max_tokens <= 0:
            return 0.0
        return self.total / self.max_tokens


@dataclass(frozen=True)
class MetricsSnapshot:
    """Typed view over the metrics payload emitted in query responses."""

    token_usage: TokenUsageSnapshot | None = None
    errors: Sequence[object] | None = None

    @staticmethod
    def _to_float(value: object) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        return None

    @classmethod
    def from_mapping(cls, metrics: Mapping[str, object]) -> "MetricsSnapshot":
        token_usage_data = metrics.get("token_usage")
        token_usage: TokenUsageSnapshot | None = None
        if isinstance(token_usage_data, Mapping):
            total = cls._to_float(token_usage_data.get("total"))
            max_tokens = cls._to_float(token_usage_data.get("max_tokens"))
            if total is not None and max_tokens is not None:
                token_usage = TokenUsageSnapshot(total=total, max_tokens=max_tokens)

        errors_data = metrics.get("errors")
        errors: Sequence[object] | None = None
        if isinstance(errors_data, Sequence) and not isinstance(errors_data, (str, bytes)):
            errors = tuple(errors_data)

        return cls(token_usage=token_usage, errors=errors)


def calculate_result_confidence(result: QueryResponse) -> float:
    """Compute a naive confidence score for a query result."""
    confidence = 0.5

    if getattr(result, "citations", None):
        citation_count = len(result.citations)
        confidence += min(0.3, 0.05 * citation_count)

    if getattr(result, "reasoning", None):
        reasoning_length = len(result.reasoning)
        confidence += min(0.2, 0.01 * reasoning_length)

    metrics_snapshot = MetricsSnapshot()
    metrics_payload = getattr(result, "metrics", None)
    if isinstance(metrics_payload, Mapping):
        metrics_snapshot = MetricsSnapshot.from_mapping(metrics_payload)

    token_usage = metrics_snapshot.token_usage
    if token_usage is not None:
        ratio = token_usage.utilization_ratio
        if 0.3 <= ratio <= 0.9:
            confidence += 0.1
        elif ratio > 0.9:
            confidence -= 0.1

    errors = metrics_snapshot.errors
    if errors:
        error_count = len(errors)
        confidence -= min(0.4, 0.1 * error_count)

    return max(0.1, min(1.0, confidence))


T = TypeVar("T")


def enqueue_with_limit(queue: Deque[T], item: T, limit: int) -> bool:
    """Append an item if the queue is below a size limit.

    Args:
        queue: Target queue to append to.
        item: Item to enqueue.
        limit: Maximum allowed queue size.

    Returns:
        ``True`` when the item is enqueued, ``False`` when dropped.

    Raises:
        ValueError: If ``limit`` is not positive.
    """

    if limit <= 0:
        raise ValueError("limit must be positive")
    if len(queue) >= limit:
        return False
    queue.append(item)
    return True
