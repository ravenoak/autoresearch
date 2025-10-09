# mypy: ignore-errors
"""Tests for storage delegation and message queue configuration."""

from typing import Any
from autoresearch import storage


class DummyStorage(storage.StorageManager):
    """Minimal StorageManager subclass for delegation tests."""


class MockStorageQueue:
    """Mock storage queue that implements StorageQueueProtocol."""

    def __init__(self) -> None:
        self.items: list[Any] = []

    def put(self, item: Any) -> None:
        """Add item to queue."""
        self.items.append(item)


def test_set_and_get_delegate():
    """Storage delegate should be set and retrieved globally."""
    storage.set_delegate(DummyStorage)
    try:
        assert storage.get_delegate() is DummyStorage
    finally:
        storage.set_delegate(None)
    assert storage.get_delegate() is None


def test_set_message_queue():
    """Message queue can be configured and cleared."""
    queue = MockStorageQueue()
    storage.set_message_queue(queue)
    assert storage._message_queue is queue
    storage.set_message_queue(None)
    assert storage._message_queue is None
