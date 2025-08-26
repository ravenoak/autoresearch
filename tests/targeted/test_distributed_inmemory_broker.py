from autoresearch.distributed.broker import InMemoryBroker


def test_inmemory_broker_publish_and_shutdown():
    broker = InMemoryBroker()
    broker.publish({"hello": "world"})
    assert not broker.queue.empty()
    broker.shutdown()
