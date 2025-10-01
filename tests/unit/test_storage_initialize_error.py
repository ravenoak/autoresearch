from __future__ import annotations

import pytest

from autoresearch import storage
from autoresearch.errors import StorageError


def test_initialize_storage_missing_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_setup(
        db_path: str | None,
        context: storage.StorageContext,
        state: storage.StorageState,
    ) -> None:
        del db_path, context, state

    monkeypatch.setattr(storage, "setup", fake_setup)
    ctx: storage.StorageContext = storage.StorageContext()
    with pytest.raises(StorageError):
        storage.initialize_storage(":memory:", context=ctx)
