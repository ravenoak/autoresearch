import sys
import types

# Stub heavy modules before importing distributed
sys.modules.setdefault("ray", types.SimpleNamespace(remote=lambda f: f))
sys.modules.setdefault(
    "autoresearch.orchestration.state",
    types.SimpleNamespace(QueryState=object)
)
sys.modules.setdefault(
    "autoresearch.orchestration.orchestrator",
    types.SimpleNamespace(AgentFactory=object)
)
sys.modules.setdefault("autoresearch.models", types.SimpleNamespace())

from autoresearch.distributed import (  # noqa: E402
    get_message_broker,
    RedisQueue,
    InMemoryBroker,
)


class FakeRedis:
    def __init__(self):
        self.list = []

    def rpush(self, name, value):
        self.list.append(value)

    def blpop(self, names):
        return names[0], self.list.pop(0).encode()

    def close(self):
        pass


def test_get_message_broker_default():
    broker = get_message_broker(None)
    assert isinstance(broker, InMemoryBroker)
    broker.shutdown()


def test_redis_queue_roundtrip():
    client = FakeRedis()
    queue = RedisQueue(client, "q")
    queue.put({"a": 1})
    assert queue.get() == {"a": 1}
