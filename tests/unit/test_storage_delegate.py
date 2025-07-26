from queue import Queue

from autoresearch.storage import (
    StorageManager,
    set_delegate,
    get_delegate,
    set_message_queue,
)


class DummyStorage(StorageManager):
    called = False

    @staticmethod
    def setup(db_path=None):
        DummyStorage.called = True


def test_set_and_get_delegate():
    set_delegate(DummyStorage)
    assert get_delegate() is DummyStorage


def test_delegate_setup_called():
    set_delegate(DummyStorage)
    StorageManager.setup("path")
    assert DummyStorage.called
    set_delegate(None)


def test_message_queue_put():
    q = Queue()
    set_message_queue(q)
    StorageManager.persist_claim({"id": "1", "content": "c"})
    msg = q.get_nowait()
    assert msg["action"] == "persist_claim"
    set_message_queue(None)
