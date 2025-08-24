import pytest

from autoresearch.distributed.broker import RedisBroker

redis = pytest.importorskip("redis")

pytestmark = [pytest.mark.slow, pytest.mark.requires_distributed]


class FakeRedis:
    def __init__(self) -> None:
        self.items: list[str] = []

    def rpush(self, name: str, value: str) -> None:  # pragma: no cover - simple
        self.items.append(value)

    def blpop(self, names: list[str]):
        return names[0], self.items.pop(0).encode()

    def close(self) -> None:  # pragma: no cover - no-op
        pass


def test_redis_broker_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(redis.Redis, "from_url", lambda url: fake)
    broker = RedisBroker("redis://localhost:6379/0", queue_name="test")
    broker.publish({"a": 1})
    msg = broker.queue.get()
    assert msg == {"a": 1}
