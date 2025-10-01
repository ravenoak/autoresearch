from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from types import ModuleType
from typing import Any, TYPE_CHECKING

import pytest


if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from autoresearch.storage_typing import JSONDict
else:  # pragma: no cover - runtime fallback when package is unavailable
    JSONDict = Mapping[str, Any]


class _StorageManagerStub:
    """Minimal drop-in replacement for :class:`autoresearch.storage.StorageManager`."""

    @staticmethod
    def persist_claim(claim: Mapping[str, Any] | JSONDict) -> None:  # pragma: no cover - stub
        """Accept a claim payload without persisting it."""

        return None

    @staticmethod
    def setup(
        *,
        db_path: str | None = None,
        context: object | None = None,
        state: object | None = None,
    ) -> "_StorageManagerStub":  # pragma: no cover - stub
        """Mimic the storage initialisation call."""

        return _StorageManagerStub()


@pytest.fixture()
def dummy_storage(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Register a no-op ``autoresearch.storage`` module for tests.

    The stub provides a minimal ``StorageManager`` with the methods used by
    tests and ensures calls to ``setup`` are harmless.
    """
    module = ModuleType("autoresearch.storage")

    def _setup_stub(
        *,
        db_path: str | None = None,
        context: object | None = None,
        state: object | None = None,
    ) -> _StorageManagerStub:
        return _StorageManagerStub()

    setup_stub: Callable[..., _StorageManagerStub] = _setup_stub
    setattr(module, "StorageManager", _StorageManagerStub)
    setattr(module, "setup", setup_stub)
    monkeypatch.setitem(sys.modules, "autoresearch.storage", module)
    return module
