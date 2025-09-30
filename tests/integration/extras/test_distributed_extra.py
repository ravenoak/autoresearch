"""Tests for the distributed optional extra."""

from __future__ import annotations

from typing import Any, cast

import pytest

from autoresearch.distributed.broker import AgentResultMessage, get_message_broker


def _make_agent_result_message(result: dict[str, Any] | None = None) -> AgentResultMessage:
    return {
        "action": "agent_result",
        "agent": "agent",
        "result": result or {"k": "v"},
        "pid": 1234,
    }


@pytest.mark.requires_distributed
def test_inmemory_broker_roundtrip() -> None:
    """The distributed extra adds message brokers."""
    broker = get_message_broker("memory")
    expected = _make_agent_result_message()
    broker.publish(expected)
    message = cast(AgentResultMessage, broker.queue.get())
    assert message == expected
    broker.shutdown()
