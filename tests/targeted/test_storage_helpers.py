"""Tests for lightweight helpers in :mod:`autoresearch.storage`."""

import sys
import types

sys.modules.setdefault(
    "pydantic_settings",
    types.SimpleNamespace(BaseSettings=object, CliApp=object, SettingsConfigDict=dict),
)

from autoresearch import storage  # noqa: E402


class DummyManager(storage.StorageManager):
    """Minimal delegate for testing injection."""


def test_delegate_injection():
    """`set_delegate` registers a custom `StorageManager` implementation."""
    storage.set_delegate(DummyManager)
    try:
        assert storage.get_delegate() is DummyManager
    finally:
        storage.set_delegate(None)


def test_message_queue_assignment():
    """`set_message_queue` updates the global queue reference."""
    queue = object()
    storage.set_message_queue(queue)
    try:
        assert storage._message_queue is queue
    finally:
        storage.set_message_queue(None)
