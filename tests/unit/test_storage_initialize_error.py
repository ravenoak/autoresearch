import pytest

from autoresearch import storage
from autoresearch.errors import StorageError


def test_initialize_storage_missing_backend(monkeypatch):
    def fake_setup(db_path, context, state):
        pass

    monkeypatch.setattr(storage, "setup", fake_setup)
    ctx = storage.StorageContext()
    with pytest.raises(StorageError):
        storage.initialize_storage(":memory:", context=ctx)
