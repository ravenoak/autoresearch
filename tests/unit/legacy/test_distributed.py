# mypy: ignore-errors
import pytest

from autoresearch.distributed import InMemoryBroker, publish_claim, get_message_broker

pytestmark = [pytest.mark.requires_distributed]


def test_get_message_broker_invalid() -> None:
    with pytest.raises(ValueError):
        get_message_broker("unknown")


@pytest.mark.skip(reason="multiprocessing Manager unsupported in this environment")
def test_publish_claim_inmemory() -> None:
    broker = InMemoryBroker()
    publish_claim(broker, {"a": 1}, True)
    msg = broker.queue.get()
    assert msg == {"action": "persist_claim", "claim": {"a": 1}, "partial_update": True}
    broker.shutdown()
