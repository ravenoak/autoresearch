import sys
import types

import pytest

# Stub heavy modules before importing distributed
sys.modules.setdefault("ray", types.SimpleNamespace(remote=lambda f: f))
sys.modules.setdefault("autoresearch.orchestration.state", types.SimpleNamespace(QueryState=object))
sys.modules.setdefault(
    "autoresearch.orchestration.orchestrator", types.SimpleNamespace(AgentFactory=object)
)
sys.modules.setdefault("autoresearch.models", types.SimpleNamespace())

from autoresearch.distributed import (  # noqa: E402
    get_message_broker,
    RedisQueue,
    InMemoryBroker,
)


def test_get_message_broker_default():
    broker = get_message_broker(None)
    assert isinstance(broker, InMemoryBroker)
    broker.shutdown()


@pytest.mark.requires_distributed
def test_redis_queue_roundtrip(redis_client):
    queue = RedisQueue(redis_client, "q")
    queue.put({"a": 1})
    assert queue.get() == {"a": 1}
