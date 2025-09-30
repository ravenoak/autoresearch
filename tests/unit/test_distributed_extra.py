import pytest

from tests.helpers.modules import ensure_stub_module
from typing import Any

# Stub heavy modules before importing distributed
ensure_stub_module("ray", {"remote": lambda f: f})
ensure_stub_module("autoresearch.orchestration.state", {"QueryState": object})
ensure_stub_module(
    "autoresearch.orchestration.orchestrator", {"AgentFactory": object}
)
ensure_stub_module("autoresearch.models")

from autoresearch.distributed import (  # noqa: E402
    get_message_broker,
    RedisQueue,
    InMemoryBroker,
)

pytestmark = [
    pytest.mark.requires_distributed,
    pytest.mark.skip(reason="multiprocessing Manager unsupported in this environment"),
]


def test_get_message_broker_default() -> None:
    broker = get_message_broker(None)
    assert isinstance(broker, InMemoryBroker)
    broker.shutdown()


@pytest.mark.redis
def test_redis_queue_roundtrip(redis_client: Any) -> None:
    queue = RedisQueue(redis_client, "q")
    queue.put({"a": 1})
    assert queue.get() == {"a": 1}
