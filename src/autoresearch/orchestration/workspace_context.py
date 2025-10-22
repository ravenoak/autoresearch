"""Runtime context helpers for workspace-scoped orchestration hints."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Mapping

import contextvars

_workspace_hints_var: contextvars.ContextVar[Mapping[str, Any] | None]
_workspace_hints_var = contextvars.ContextVar("workspace_hints", default=None)


def get_active_workspace_hints() -> Mapping[str, Any] | None:
    """Return the workspace hint mapping active for the current context."""

    return _workspace_hints_var.get()


@contextmanager
def use_workspace_hints(hints: Mapping[str, Any] | None) -> Iterator[None]:
    """Temporarily activate *hints* for the current execution context."""

    token = _workspace_hints_var.set(hints)
    try:
        yield
    finally:
        _workspace_hints_var.reset(token)


__all__ = ["get_active_workspace_hints", "use_workspace_hints"]
