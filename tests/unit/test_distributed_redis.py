import sys
import types

import pytest

from autoresearch.distributed import get_message_broker


class _FakeRedisClient:
    def __init__(self) -> None:
        self.entries: list[tuple[str, str]] = []

    def rpush(self, name: str, value: str) -> None:
        self.entries.append((name, value))

    def blpop(self, names):
        name = names[0]
        return name, self.entries.pop(0)[1].encode()

    def close(self) -> None:  # pragma: no cover - no side effects
        pass


def test_get_message_broker_redis_roundtrip(monkeypatch):
    client = _FakeRedisClient()
    dummy_module = types.SimpleNamespace(
        Redis=types.SimpleNamespace(from_url=lambda url: client)
    )
    monkeypatch.setitem(sys.modules, "redis", dummy_module)

    broker = get_message_broker("redis")
    broker.publish({"a": 1})
    assert client.entries[0][0] == "autoresearch"
    assert client.entries[0][1] == "{\"a\": 1}"
    broker.shutdown()


def test_get_message_broker_redis_missing(monkeypatch):
    sys.modules.pop("redis", None)
    with pytest.raises(ModuleNotFoundError):
        get_message_broker("redis")
