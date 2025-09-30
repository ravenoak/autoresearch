import pytest

from autoresearch import storage


@pytest.mark.requires_vss
def test_has_vss_with_dummy_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """StorageManager.has_vss should reflect backend capability."""

    class DummyBackend:
        def __init__(self, flag: bool) -> None:
            self._flag = flag

        def has_vss(self) -> bool:
            return self._flag

    storage.StorageManager.context.db_backend = DummyBackend(True)
    assert storage.StorageManager.has_vss() is True
    storage.StorageManager.context.db_backend = DummyBackend(False)
    assert storage.StorageManager.has_vss() is False
    storage.StorageManager.context.db_backend = None
