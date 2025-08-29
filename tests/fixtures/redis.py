from __future__ import annotations

import pytest


@pytest.fixture()
def redis_client(redis_service):
    """Return a Redis client backed by the session-level service."""
    redis_service.flushdb()
    yield redis_service
