import sys
import types

import pytest

from autoresearch.distributed import get_message_broker

pytestmark = [pytest.mark.requires_distributed, pytest.mark.redis]


def test_get_message_broker_redis_roundtrip(monkeypatch, redis_client):
    """Round trip messages through the Redis broker."""

    dummy_module = types.SimpleNamespace(
        Redis=types.SimpleNamespace(from_url=lambda url: redis_client)
    )
    monkeypatch.setitem(sys.modules, "redis", dummy_module)

    broker = get_message_broker("redis")
    broker.publish({"a": 1})
    assert redis_client.lrange("autoresearch", 0, -1)[0] == b'{"a": 1}'
    broker.shutdown()


def test_get_message_broker_redis_missing(monkeypatch):
    """Raise an error when the Redis module cannot be imported."""

    monkeypatch.setitem(sys.modules, "redis", None)
    with pytest.raises(ModuleNotFoundError):
        get_message_broker("redis")
