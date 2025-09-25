"""Common interfaces shared across the project.

Spec: docs/specs/interfaces.md
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Callable, Protocol, runtime_checkable

from .models import QueryResponse

CallbackMap = Mapping[str, Callable[..., object]]


@runtime_checkable
class QueryStateLike(Protocol):
    """Protocol for orchestration state objects."""

    cycle: int

    def update(self, result: Mapping[str, object]) -> None:
        """Update state with agent result."""

    def synthesize(self) -> QueryResponse:
        """Produce a final response."""
