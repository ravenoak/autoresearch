from __future__ import annotations

import pytest

try:  # pragma: no cover - optional dependency
    import redis
except Exception:  # pragma: no cover - redis optional
    redis = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import fakeredis
except Exception:  # pragma: no cover - fakeredis optional
    fakeredis = None  # type: ignore[assignment]


@pytest.fixture()
def redis_client():
    """Return a Redis client, preferring a real server when available."""

    if redis is not None:
        try:
            client = redis.Redis.from_url(
                "redis://localhost:6379/0", socket_connect_timeout=1
            )
            client.ping()
            client.flushdb()
            yield client
            client.close()
            return
        except Exception:  # pragma: no cover - fall back to fakeredis
            pass
    if fakeredis is not None:
        client = fakeredis.FakeStrictRedis()
        client.flushdb()
        yield client
        client.close()
        return
    pytest.skip("Redis service not available")
