from __future__ import annotations

import importlib.util
from typing import Any, cast

import pytest

from autoresearch.distributed.broker import AgentResultMessage, RedisBroker

if importlib.util.find_spec("redis") is None:
    pytest.skip("redis not installed", allow_module_level=True)
import redis

pytestmark = [
    pytest.mark.slow,
    pytest.mark.requires_distributed,
    pytest.mark.redis,
]


def _make_agent_result_message(result: dict[str, Any] | None = None) -> AgentResultMessage:
    return {
        "action": "agent_result",
        "agent": "agent",
        "result": result or {"value": 1},
        "pid": 1234,
    }


def test_redis_broker_roundtrip(
    monkeypatch: pytest.MonkeyPatch, redis_client: object
) -> None:
    def _from_url(url: str) -> object:
        return redis_client

    monkeypatch.setattr(redis.Redis, "from_url", _from_url)
    broker = RedisBroker("redis://localhost:6379/0", queue_name="test")
    expected = _make_agent_result_message(result={"value": 1})
    broker.publish(expected)
    message = cast(AgentResultMessage, broker.queue.get())
    assert message == expected
