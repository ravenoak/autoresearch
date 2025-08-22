"""Utilities for retrying operations with exponential backoff.

This module offers a small helper for recovering from transient errors. It
attempts an action multiple times, sleeping for an exponentially increasing
interval between tries.
"""

from __future__ import annotations

import time
from typing import Callable


def retry_with_backoff(
    action: Callable[[], bool],
    *,
    max_retries: int = 5,
    base_delay: float = 0.1,
) -> int:
    """Retry ``action`` until it succeeds or the retry limit is reached.

    Args:
        action: Callable returning ``True`` on success.
        max_retries: Maximum number of attempts.
        base_delay: Delay in seconds for the first retry.

    Returns:
        Number of attempts made.

    Raises:
        RuntimeError: If ``action`` fails after ``max_retries`` attempts.
    """

    for attempt in range(1, max_retries + 1):
        if action():
            return attempt
        time.sleep(base_delay * (2 ** (attempt - 1)))
    raise RuntimeError("action failed after retries")
