from __future__ import annotations

from autoresearch.distributed.broker import (
    BrokerMessage,
    InMemoryBroker,
    STOP_MESSAGE,
    StorageBrokerQueueProtocol,
)

from tests.targeted.helpers.distributed import build_agent_result_message


def test_inmemory_broker_publish_and_shutdown() -> None:
    broker = InMemoryBroker()
    agent_message = build_agent_result_message(result={"value": 2})
    broker.publish(agent_message)
    queue: StorageBrokerQueueProtocol = broker.queue
    retrieved: BrokerMessage = queue.get()
    assert retrieved == agent_message
    broker.publish(STOP_MESSAGE)
    stop_message: BrokerMessage = broker.queue.get()
    assert stop_message["action"] == "stop"
    broker.shutdown()
