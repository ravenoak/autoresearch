import sys
import types

import pytest


@pytest.fixture()
def dummy_storage(monkeypatch: pytest.MonkeyPatch):
    """Register a no-op ``autoresearch.storage`` module for tests.

    The stub provides a minimal ``StorageManager`` with the methods used by
    tests and ensures calls to ``setup`` are harmless.
    """
    module = types.ModuleType("autoresearch.storage")

    class StorageManager:
        @staticmethod
        def persist_claim(claim) -> None:  # pragma: no cover - no-op
            pass

        @staticmethod
        def setup(*_args, **_kwargs) -> None:  # pragma: no cover - no-op
            pass

    setattr(module, "StorageManager", StorageManager)
    setattr(module, "setup", lambda *_a, **_k: None)
    monkeypatch.setitem(sys.modules, "autoresearch.storage", module)
    return module
