"""In-memory registry for preserving query state snapshots between runs."""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass
from threading import RLock
from typing import Any, Optional, Protocol, TypeVar
from uuid import uuid4

from ..config.models import ConfigModel
from .state import QueryState


_SupportsModelCopySelf = TypeVar("_SupportsModelCopySelf", bound="_SupportsModelCopy")


class _SupportsModelCopy(Protocol):
    """Typed protocol for objects exposing ``model_copy``."""

    def model_copy(
        self: _SupportsModelCopySelf,
        *,
        update: Mapping[str, Any] | None = None,
        deep: bool | None = None,
        **kwargs: Any,
    ) -> _SupportsModelCopySelf:
        """Return a deep copy of the model."""


_ModelT = TypeVar("_ModelT", bound=_SupportsModelCopy)


def _clone_model(
    model: _ModelT, *, memo: dict[int, Any] | None = None
) -> _ModelT:
    """Return a deep copy of ``model`` using its ``model_copy`` method."""

    if memo is None:
        return model.model_copy(deep=True)
    try:
        return model.model_copy(deep=True, memo=memo)
    except TypeError:
        return model.model_copy(deep=True)


@dataclass
class QueryStateSnapshot:
    """Container storing a deep copy of a query state and its config."""

    state: QueryState
    config: ConfigModel
    created_at: float
    updated_at: float

    def clone(self) -> "QueryStateSnapshot":
        """Return a deep copy of this snapshot."""

        memo: dict[int, Any] = {}
        return QueryStateSnapshot(
            state=_clone_model(self.state, memo=memo),
            config=_clone_model(self.config),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class QueryStateRegistry:
    """LRU registry for :class:`QueryState` instances."""

    _lock = RLock()
    _store: "OrderedDict[str, QueryStateSnapshot]" = OrderedDict()
    _max_entries: int = 32

    @classmethod
    def register(cls, state: QueryState, config: ConfigModel) -> str:
        """Store a snapshot and return its identifier.

        Args:
            state: Final state produced by the orchestrator.
            config: Configuration used for the run.

        Returns:
            Unique identifier that can be used to fetch the snapshot later.
        """

        memo: dict[int, Any] = {}
        snapshot = QueryStateSnapshot(
            state=_clone_model(state, memo=memo),
            config=_clone_model(config),
            created_at=time.time(),
            updated_at=time.time(),
        )
        state_id = uuid4().hex
        with cls._lock:
            cls._store[state_id] = snapshot
            cls._store.move_to_end(state_id)
            cls._trim_if_needed()
        return state_id

    @classmethod
    def clone(cls, state_id: str) -> Optional[tuple[QueryState, ConfigModel]]:
        """Return deep copies of the stored state and config."""

        with cls._lock:
            snapshot = cls._store.get(state_id)
            if snapshot is None:
                return None
            snapshot.updated_at = time.time()
            cls._store.move_to_end(state_id)
            cloned = snapshot.clone()
        cloned.state._ensure_lock()
        return cloned.state, cloned.config

    @classmethod
    def update(
        cls,
        state_id: str,
        state: QueryState,
        config: Optional[ConfigModel] = None,
    ) -> None:
        """Replace the stored snapshot for ``state_id``."""

        with cls._lock:
            existing = cls._store.get(state_id)
            if existing is None:
                effective_config = config or ConfigModel()
                memo: dict[int, Any] = {}
                new_snapshot = QueryStateSnapshot(
                    state=_clone_model(state, memo=memo),
                    config=_clone_model(effective_config),
                    created_at=time.time(),
                    updated_at=time.time(),
                )
                cls._store[state_id] = new_snapshot
            else:
                memo: dict[int, Any] = {}
                existing.state = _clone_model(state, memo=memo)
                existing.state._ensure_lock()
                if config is not None:
                    existing.config = _clone_model(config)
                existing.updated_at = time.time()
            cls._store.move_to_end(state_id)
            cls._trim_if_needed()

    @classmethod
    def get_snapshot(cls, state_id: str) -> Optional[QueryStateSnapshot]:
        """Return a clone of the stored snapshot for inspection."""

        with cls._lock:
            snapshot = cls._store.get(state_id)
            if snapshot is None:
                return None
            cls._store.move_to_end(state_id)
            snapshot.updated_at = time.time()
            clone = snapshot.clone()
        clone.state._ensure_lock()
        return clone

    @classmethod
    def _trim_if_needed(cls) -> None:
        """Evict least-recently-used snapshots when exceeding the limit."""

        while len(cls._store) > cls._max_entries:
            cls._store.popitem(last=False)


__all__ = ["QueryStateRegistry", "QueryStateSnapshot"]
