from __future__ import annotations

import pytest

from autoresearch.storage import StorageManager, get_delegate, set_delegate


class DummyStorage(StorageManager):
    touched: list[str] = []

    @staticmethod
    def touch_node(node_id: str) -> None:  # pragma: no cover - simple delegation
        DummyStorage.touched.append(node_id)


@pytest.fixture(autouse=True)
def _reset_delegate():
    set_delegate(None)
    yield
    set_delegate(None)


def test_touch_node_uses_delegate() -> None:
    set_delegate(DummyStorage)
    StorageManager.touch_node("n1")
    assert DummyStorage.touched == ["n1"]
    assert get_delegate() is DummyStorage
