# mypy: ignore-errors
from __future__ import annotations

import importlib.util
from typing import Any, Mapping, cast

import pytest

from autoresearch.distributed.broker import (
    AgentResultMessage,
    BrokerMessage,
    MessageQueueProtocol,
    RedisBroker,
    StorageBrokerQueueProtocol,
)

if importlib.util.find_spec("redis") is None:
    pytest.skip("redis not installed", allow_module_level=True)
import redis

pytestmark = [
    pytest.mark.slow,
    pytest.mark.requires_distributed,
    pytest.mark.redis,
]


def _make_agent_result_message(
    result: Mapping[str, Any] | None = None,
) -> AgentResultMessage:
    payload: AgentResultMessage = {
        "action": "agent_result",
        "agent": "agent",
        "result": dict(result or {"value": 1}),
        "pid": 1234,
    }
    return payload


def test_redis_broker_roundtrip(
    monkeypatch: pytest.MonkeyPatch, redis_client: object
) -> None:
    def _from_url(url: str, *args: object, **kwargs: object) -> object:
        del url, args, kwargs
        return redis_client

    monkeypatch.setattr(redis.Redis, "from_url", _from_url)
    broker = RedisBroker("redis://localhost:6379/0", queue_name="test")
    expected: AgentResultMessage = _make_agent_result_message(result={"value": 1})
    broker.publish(expected)
    queue: StorageBrokerQueueProtocol = broker.queue
    queue_protocol: MessageQueueProtocol = queue
    message: BrokerMessage = queue_protocol.get()
    assert cast(AgentResultMessage, message) == expected
