from __future__ import annotations

import sys
import types
from typing import Iterator

import pytest


@pytest.fixture()
def dummy_storage(monkeypatch: pytest.MonkeyPatch) -> Iterator[types.ModuleType]:
    """Register a minimal ``autoresearch.storage`` stub for tests.

    The fixture installs a lightweight module with a ``StorageManager`` and
    ``setup`` function so that tests depending on the storage layer can import
    ``autoresearch.storage`` without touching real storage backends.
    """
    module = types.ModuleType("autoresearch.storage")

    class StorageManager:  # pragma: no cover - simple stub
        @staticmethod
        def persist_claim(claim):
            pass

        @staticmethod
        def setup(*args, **kwargs):  # type: ignore[no-untyped-def]
            pass

    module.StorageManager = StorageManager
    module.setup = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "autoresearch.storage", module)
    try:
        yield module
    finally:
        sys.modules.pop("autoresearch.storage", None)
