from __future__ import annotations

import pytest

try:
    import fakeredis
except Exception:  # pragma: no cover - fakeredis optional
    fakeredis = None


class _InMemoryRedis:
    """Minimal Redis-like client for tests.

    Provides `rpush`, `blpop`, and `close` methods so Redis-backed
    components can be exercised without a running Redis server.
    """

    def __init__(self) -> None:
        self._items: list[str] = []

    def rpush(self, name: str, value: str) -> None:  # pragma: no cover - trivial
        self._items.append(value)

    def blpop(self, names):  # pragma: no cover - trivial
        name = names[0]
        return name, self._items.pop(0).encode()

    def lrange(self, name: str, start: int, end: int):  # pragma: no cover - trivial
        if end == -1:
            end = len(self._items) - 1
        return [v.encode() for v in self._items[start : end + 1]]

    def close(self) -> None:  # pragma: no cover - no-op
        pass


@pytest.fixture()
def redis_client():
    """Return a lightweight Redis client for tests.

    Uses `fakeredis` when available; otherwise falls back to a simple
    in-memory stub.
    """

    if fakeredis is not None:
        return fakeredis.FakeRedis()
    return _InMemoryRedis()
