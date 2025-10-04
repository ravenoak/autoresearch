from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any, cast

import pytest
from prometheus_client import CollectorRegistry

from autoresearch.distributed.broker import AgentResultMessage, RedisBroker

package = types.ModuleType("autoresearch.monitor")
package.__path__ = [str(Path(__file__).resolve().parents[2] / "src" / "autoresearch" / "monitor")]
sys.modules.setdefault("autoresearch.monitor", package)
from autoresearch.monitor.node_health import NodeHealthMonitor  # noqa: E402

pytestmark = [
    pytest.mark.slow,
    pytest.mark.requires_distributed,
    pytest.mark.redis,
]


def _make_agent_result_message(
    *,
    agent: str = "agent",
    result: dict[str, Any] | None = None,
    pid: int = 1234,
) -> AgentResultMessage:
    """Construct a minimal :class:`AgentResultMessage` for broker tests."""

    return {
        "action": "agent_result",
        "agent": agent,
        "result": result or {"status": "ok"},
        "pid": pid,
    }


class DummyRedis:
    """Minimal Redis stub supporting list operations."""

    def __init__(self) -> None:
        self._data: list[str] = []

    def rpush(self, name: str, value: str) -> None:  # pragma: no cover - trivial
        self._data.append(value)

    def blpop(self, names: list[str]) -> tuple[str, bytes]:  # pragma: no cover - trivial
        return names[0], self._data.pop(0).encode()

    def ping(self) -> bool:  # pragma: no cover - trivial
        return True

    def close(self) -> None:  # pragma: no cover - trivial
        pass


def test_redis_broker_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    import redis

    dummy = DummyRedis()

    def _from_url(url: str) -> DummyRedis:
        return dummy

    monkeypatch.setattr(redis.Redis, "from_url", _from_url)
    broker = RedisBroker("redis://localhost:6379/0", queue_name="test")
    expected = _make_agent_result_message(result={"value": 1})
    broker.publish(expected)
    message = cast(AgentResultMessage, broker.queue.get())
    assert message == expected
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
