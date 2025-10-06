# mypy: ignore-errors
from __future__ import annotations

from typing import Protocol

import pytest

from tests.typing_helpers import TypedFixture


class _RedisClientProtocol(Protocol):
    def flushdb(self) -> None: ...


@pytest.fixture()
def redis_client(
    redis_service: _RedisClientProtocol,
) -> TypedFixture[_RedisClientProtocol]:
    """Return a Redis client backed by the session-level service."""
    redis_service.flushdb()
    yield redis_service
    return None
