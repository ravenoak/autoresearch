import importlib.util

import pytest

from autoresearch.distributed.broker import RedisBroker

if importlib.util.find_spec("redis") is None:
    pytest.skip("redis not installed", allow_module_level=True)
import redis

pytestmark = [pytest.mark.slow, pytest.mark.requires_distributed]


def test_redis_broker_roundtrip(monkeypatch: pytest.MonkeyPatch, redis_client) -> None:
    monkeypatch.setattr(redis.Redis, "from_url", lambda url: redis_client)
    broker = RedisBroker("redis://localhost:6379/0", queue_name="test")
    broker.publish({"a": 1})
    msg = broker.queue.get()
    assert msg == {"a": 1}
