from __future__ import annotations

import contextlib
import logging
from typing import Generator

from multiprocessing import resource_tracker

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _log_resource_tracker_cache() -> Generator[None, None, None]:
    """Log resource tracker state before and after each test.

    The diagnostics help confirm that multiprocessing resources are removed
    during fixture cleanup and highlight any residual entries.
    """
    with contextlib.suppress(Exception):
        cache = resource_tracker._resource_tracker._cache  # type: ignore[attr-defined]
        before = cache.copy()
        if before:
            logger.debug("resource tracker pre-test: %s", before)
    yield
    with contextlib.suppress(Exception):
        cache = resource_tracker._resource_tracker._cache  # type: ignore[attr-defined]
        if cache:
            logger.debug("resource tracker post-test: %s", cache.copy())
            cache.clear()
