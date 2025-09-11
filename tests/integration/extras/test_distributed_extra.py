"""Tests for the distributed optional extra."""

from __future__ import annotations

import pytest

from autoresearch.distributed.broker import get_message_broker


@pytest.mark.requires_distributed
def test_inmemory_broker_roundtrip() -> None:
    """The distributed extra adds message brokers."""
    broker = get_message_broker("memory")
    broker.publish({"k": "v"})
    assert broker.queue.get()["k"] == "v"
    broker.shutdown()
