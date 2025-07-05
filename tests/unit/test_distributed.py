import pytest

from autoresearch.distributed import InMemoryBroker, publish_claim, get_message_broker


def test_get_message_broker_invalid():
    with pytest.raises(ValueError):
        get_message_broker("unknown")


def test_publish_claim_inmemory():
    broker = InMemoryBroker()
    publish_claim(broker, {"a": 1}, True)
    msg = broker.queue.get()
    assert msg == {"action": "persist_claim", "claim": {"a": 1}, "partial_update": True}
    broker.shutdown()
