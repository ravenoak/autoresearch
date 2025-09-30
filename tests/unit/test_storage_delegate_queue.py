"""Tests for storage delegation and message queue configuration."""

from autoresearch import storage


class DummyStorage(storage.StorageManager):
    """Minimal StorageManager subclass for delegation tests."""


def test_set_and_get_delegate() -> None:
    """Storage delegate should be set and retrieved globally."""
    storage.set_delegate(DummyStorage)
    try:
        assert storage.get_delegate() is DummyStorage
    finally:
        storage.set_delegate(None)
    assert storage.get_delegate() is None


def test_set_message_queue() -> None:
    """Message queue can be configured and cleared."""
    queue = object()
    storage.set_message_queue(queue)
    assert storage._message_queue is queue
    storage.set_message_queue(None)
    assert storage._message_queue is None
