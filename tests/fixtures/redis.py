from __future__ import annotations

import pytest

from tests.typing_helpers import TypedFixture


@pytest.fixture()
def redis_client(redis_service) -> TypedFixture[object]:
    """Return a Redis client backed by the session-level service."""
    redis_service.flushdb()
    yield redis_service
