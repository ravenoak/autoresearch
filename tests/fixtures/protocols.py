# mypy: ignore-errors
"""Shared typing utilities for fixture stubs.

This module centralises lightweight protocols and dataclasses used by
``tests/fixtures`` so individual fixtures can share well-typed helpers
without re-declaring structural contracts.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Protocol


JSONMapping = Mapping[str, Any]


class StorageManagerProtocol(Protocol):
    """Protocol describing the subset of ``StorageManager`` used in tests."""

    @staticmethod
    def persist_claim(claim: JSONMapping) -> None: ...

    @staticmethod
    def setup(
        *,
        db_path: str | None = ...,  # pragma: no cover - typing helper
        context: object | None = ...,  # pragma: no cover - typing helper
        state: object | None = ...,  # pragma: no cover - typing helper
    ) -> "StorageManagerProtocol": ...


StorageSetup = Callable[..., StorageManagerProtocol]


class StorageModuleProtocol(Protocol):
    """Protocol for the dynamically-created ``autoresearch.storage`` module."""

    StorageManager: type[StorageManagerProtocol]
    setup: StorageSetup


@dataclass(slots=True)
class StorageHandle:
    """Dataclass capturing the exported handles from the storage stub."""

    module: ModuleType
    manager: type[StorageManagerProtocol]
    setup: StorageSetup


ModuleLoader = Callable[[str], ModuleType | None]
ExtraValidator = Callable[[ModuleType], bool]


@dataclass(frozen=True, slots=True)
class ExtraProbe:
    """Describe how to detect whether an optional extra is available."""

    modules: Sequence[str]
    validator: ExtraValidator | None = None

    def available(self, loader: ModuleLoader) -> bool:
        """Return ``True`` when all modules load and validators pass."""

        for module_name in self.modules:
            module = loader(module_name)
            if module is None:
                return False
            if self.validator is not None and not self.validator(module):
                return False
        return True
