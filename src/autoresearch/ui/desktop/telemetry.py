"""Desktop telemetry helpers for UI analytics instrumentation."""

from __future__ import annotations

import json
import threading
from typing import Any, Callable, Mapping, MutableMapping, Optional

from PySide6.QtCore import QLoggingCategory, qCInfo, qCWarning

Dispatcher = Callable[[str, Mapping[str, Any]], None]

_dispatcher_lock = threading.Lock()
_dispatcher: Optional[Dispatcher] = None


def _initialise_dispatcher() -> None:
    """Attempt to discover the analytics dispatcher at import time."""

    try:
        from ... import analytics as analytics_module  # type: ignore
    except Exception:  # pragma: no cover - graceful fallback
        return

    dispatch_fn = getattr(analytics_module, "dispatch_event", None)
    if callable(dispatch_fn):
        set_dispatcher(dispatch_fn)


def set_dispatcher(dispatcher: Optional[Dispatcher]) -> None:
    """Register an analytics dispatcher for telemetry forwarding."""

    global _dispatcher
    with _dispatcher_lock:
        _dispatcher = dispatcher


def get_dispatcher() -> Optional[Dispatcher]:
    """Return the currently configured analytics dispatcher."""

    with _dispatcher_lock:
        return _dispatcher


class DesktopTelemetry:
    """Emit desktop UI telemetry via Qt logging and optional analytics."""

    def __init__(self, category_name: str = "autoresearch.ui.desktop") -> None:
        self._category = QLoggingCategory(category_name)

    def emit(self, event: str, payload: Optional[Mapping[str, Any]] = None) -> None:
        """Record an analytics event."""

        payload_dict: MutableMapping[str, Any] = dict(payload or {})
        message = event
        if payload_dict:
            try:
                serialised = json.dumps(payload_dict, default=str, sort_keys=True)
            except TypeError:
                serialised = str(payload_dict)
            message = f"{event} {serialised}"

        qCInfo(self._category, message)

        dispatcher = get_dispatcher()
        if not dispatcher:
            return

        try:
            dispatcher(event, dict(payload_dict))
        except Exception as exc:  # pragma: no cover - defensive logging
            qCWarning(
                self._category,
                f"Failed to dispatch analytics event '{event}': {exc}",
            )


telemetry = DesktopTelemetry()

_initialise_dispatcher()

__all__ = ["DesktopTelemetry", "telemetry", "set_dispatcher", "get_dispatcher"]
