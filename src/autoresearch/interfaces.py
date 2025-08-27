"""Common interfaces shared across the project."""

from __future__ import annotations

from typing import Any, Callable, Dict, Protocol, runtime_checkable

from .models import QueryResponse

CallbackMap = Dict[str, Callable[..., None]]


@runtime_checkable
class QueryStateLike(Protocol):
    """Protocol for orchestration state objects."""

    cycle: int

    def update(self, result: Dict[str, Any]) -> None:
        """Update state with agent result."""

    def synthesize(self) -> QueryResponse:
        """Produce a final response."""
