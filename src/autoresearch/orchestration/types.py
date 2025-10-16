"""Typing helpers for orchestration modules.

These aliases centralize structural types that are shared across
``orchestration`` modules. They allow strict typing without importing the
heavier runtime dependencies (for example, OpenTelemetry's tracer classes)
outside of ``typing.TYPE_CHECKING`` blocks.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from autoresearch.orchestration.state import QueryState

    # ``AgentExecutionResult`` captures the minimum contract expected from agent
    # ``execute`` implementations. The concrete object is typically a ``dict`` but a
    # mapping keeps the annotations flexible for tests that substitute custom
    # containers.
    AgentExecutionResult = Mapping[str, Any]

    # ``CallbackMap`` mirrors the callback dictionaries passed through the
    # orchestrator. Individual helpers down-cast the stored ``Callable`` into the
    # expected signature before invocation.
    CallbackMap = Mapping[str, Callable[..., object]]

    AgentStartCallback = Callable[[str, QueryState], None]
    AgentEndCallback = Callable[[str, AgentExecutionResult, QueryState], None]
    CycleCallback = Callable[[int, QueryState], None]
else:
    # Runtime versions without QueryState dependency
    AgentExecutionResult = Mapping[str, Any]
    CallbackMap = Mapping[str, Callable[..., object]]
    AgentStartCallback = Callable[[str, object], None]
    AgentEndCallback = Callable[[str, AgentExecutionResult, object], None]
    CycleCallback = Callable[[int, object], None]


class TracerProtocol(Protocol):
    """Structural protocol matching the tracing API used in execution flows."""

    def start_as_current_span(
        self,
        name: str,
        *args: object,
        **kwargs: object,
    ) -> AbstractContextManager[object]:
        """Return a context manager that records a tracing span."""


__all__ = [
    "AgentExecutionResult",
    "AgentEndCallback",
    "AgentStartCallback",
    "CallbackMap",
    "CycleCallback",
    "TracerProtocol",
]
