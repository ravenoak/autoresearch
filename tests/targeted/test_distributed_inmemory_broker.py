from __future__ import annotations

from autoresearch.distributed.broker import BrokerMessage, InMemoryBroker, STOP_MESSAGE


def test_inmemory_broker_publish_and_shutdown() -> None:
    broker = InMemoryBroker()
    broker.publish(STOP_MESSAGE)
    message: BrokerMessage = broker.queue.get()
    assert message["action"] == "stop"
    broker.shutdown()
