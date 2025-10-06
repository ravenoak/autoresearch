# mypy: ignore-errors
"""Tests for the distributed optional extra."""

from __future__ import annotations

from typing import Any, cast

import pytest

from autoresearch.distributed.broker import (
    AgentResultMessage,
    BrokerMessage,
    MessageQueueProtocol,
    StorageBrokerQueueProtocol,
    get_message_broker,
)


def _make_agent_result_message(result: dict[str, Any] | None = None) -> AgentResultMessage:
    message: AgentResultMessage = {
        "action": "agent_result",
        "agent": "agent",
        "result": result or {"k": "v"},
        "pid": 1234,
    }
    return message


@pytest.mark.requires_distributed
def test_inmemory_broker_roundtrip() -> None:
    """The distributed extra adds message brokers."""
    broker = get_message_broker("memory")
    expected = _make_agent_result_message()
    broker.publish(expected)
    queue: StorageBrokerQueueProtocol = broker.queue
    queue_protocol: MessageQueueProtocol = queue
    message: BrokerMessage = queue_protocol.get()
    assert cast(AgentResultMessage, message) == expected
    broker.shutdown()
