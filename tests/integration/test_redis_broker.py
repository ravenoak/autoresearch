import sys
import types
from pathlib import Path

import pytest
from prometheus_client import CollectorRegistry

from autoresearch.distributed.broker import RedisBroker

package = types.ModuleType("autoresearch.monitor")
package.__path__ = [str(Path(__file__).resolve().parents[2] / "src" / "autoresearch" / "monitor")]
sys.modules.setdefault("autoresearch.monitor", package)
from autoresearch.monitor.node_health import NodeHealthMonitor  # noqa: E402

pytestmark = [
    pytest.mark.slow,
    pytest.mark.requires_distributed,
    pytest.mark.redis,
]


class DummyRedis:
    """Minimal Redis stub supporting list operations."""

    def __init__(self) -> None:
        self._data: list[str] = []

    def rpush(self, name: str, value: str) -> None:  # pragma: no cover - trivial
        self._data.append(value)

    def blpop(self, names: list[str]):  # pragma: no cover - trivial
        return names[0], self._data.pop(0).encode()

    def ping(self) -> bool:  # pragma: no cover - trivial
        return True

    def close(self) -> None:  # pragma: no cover - trivial
        pass


def test_redis_broker_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    import redis

    dummy = DummyRedis()
    monkeypatch.setattr(redis.Redis, "from_url", lambda url: dummy)
    broker = RedisBroker("redis://localhost:6379/0", queue_name="test")
    broker.publish({"a": 1})
    msg = broker.queue.get()
    assert msg == {"a": 1}
    registry = CollectorRegistry()
    monitor = NodeHealthMonitor(
        redis_url="redis://localhost:6379/0",
        port=None,
        interval=0.1,
        registry=registry,
    )
    monitor.check_once()
    assert registry.get_sample_value("autoresearch_redis_up") == 1.0
    assert registry.get_sample_value("autoresearch_node_health") == 1.0
    broker.shutdown()
