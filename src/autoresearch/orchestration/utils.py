from __future__ import annotations

from typing import Any, Deque

from ..models import QueryResponse


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)
    except ImportError:  # pragma: no cover - fallback path
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def calculate_result_confidence(result: QueryResponse) -> float:
    """Compute a naive confidence score for a query result."""
    confidence = 0.5

    if getattr(result, "citations", None):
        citation_count = len(result.citations)
        confidence += min(0.3, 0.05 * citation_count)

    if getattr(result, "reasoning", None):
        reasoning_length = len(result.reasoning)
        confidence += min(0.2, 0.01 * reasoning_length)

    if getattr(result, "metrics", None) and "token_usage" in result.metrics:
        tokens = result.metrics["token_usage"]
        if "total" in tokens and "max_tokens" in tokens:
            ratio = tokens["total"] / max(1, tokens["max_tokens"])
            if 0.3 <= ratio <= 0.9:
                confidence += 0.1
            elif ratio > 0.9:
                confidence -= 0.1

    if getattr(result, "metrics", None) and "errors" in result.metrics:
        error_count = len(result.metrics["errors"])
        if error_count > 0:
            confidence -= min(0.4, 0.1 * error_count)

    return max(0.1, min(1.0, confidence))


def enqueue_with_limit(queue: Deque[Any], item: Any, limit: int) -> bool:
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
