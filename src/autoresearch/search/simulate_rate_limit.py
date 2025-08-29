"""Model exponential backoff delays for HTTP retries."""

from __future__ import annotations

from typing import List


def simulate_rate_limit(backoff_factor: float = 0.2, max_retries: int = 3) -> List[float]:
    """Return delays for successive retries using exponential backoff.

    Args:
        backoff_factor: Base delay in seconds.
        max_retries: Number of retry attempts to model.

    Returns:
        List[float]: Delay before each retry attempt.
    """
    return [backoff_factor * (2**i) for i in range(max_retries)]
