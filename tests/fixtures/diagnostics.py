from __future__ import annotations

import contextlib
from multiprocessing import resource_tracker
import logging

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _log_resource_tracker_cache() -> None:
    """Log resource tracker state before and after each test.

    The diagnostics help confirm that multiprocessing resources are removed
    during fixture cleanup and highlight any residual entries.
    """
    with contextlib.suppress(Exception):
        before = resource_tracker._resource_tracker._cache.copy()  # type: ignore[attr-defined]
        if before:
            logger.debug("resource tracker pre-test: %s", before)
    yield
    with contextlib.suppress(Exception):
        after = resource_tracker._resource_tracker._cache.copy()  # type: ignore[attr-defined]
        if after:
            logger.debug("resource tracker post-test: %s", after)
