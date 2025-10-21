# mypy: ignore-errors
"""Shared typing helpers for behavior test context payloads."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, MutableMapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Optional, TypeVar, overload
from unittest.mock import MagicMock

from click.testing import Result

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator

__all__ = [
    "APICapture",
    "BehaviorContext",
    "DesktopRuntimeMocks",
    "CLIInvocation",
    "get_optional",
    "get_cli_invocation",
    "get_cli_result",
    "get_config",
    "get_orchestrator",
    "get_required",
    "set_cli_invocation",
    "set_cli_result",
    "set_value",
    "desktop_runtime",
    "StreamlitComponentMocks",
    "StreamlitTabMocks",
]

# ``MutableMapping`` rather than ``dict`` so fixtures can swap in custom
# implementations (e.g., ``defaultdict``) without breaking the type contract.
BehaviorContext = MutableMapping[str, Any]
"""Type alias for the shared mutable context passed between BDD steps."""

T = TypeVar("T")


def set_value(context: BehaviorContext, key: str, value: T) -> T:
    """Store ``value`` in ``context`` and return it.

    Keeping the return value makes it easy to use within expressions::

        result = set_value(bdd_context, "cli_result", runner.invoke(app, ["--help"]))

    Parameters
    ----------
    context:
        The shared scenario context.
    key:
        Dictionary key under which the value should be stored.
    value:
        The object to persist for later steps.
    """

    context[key] = value
    return value


@overload
def get_required(context: BehaviorContext, key: str, /) -> Any: ...


@overload
def get_required(
    context: BehaviorContext,
    key: str,
    expected_type: type[T] | tuple[type[T], ...],
    /,
) -> T: ...


def get_required(
    context: BehaviorContext,
    key: str,
    expected_type: type[T] | tuple[type[T], ...] | None = None,
) -> Any:
    """Retrieve a required value from ``context``.

    Parameters
    ----------
    context:
        Scenario context created by :func:`bdd_context`.
    key:
        Name of the value to fetch.
    expected_type:
        Optional runtime type check that will raise ``TypeError`` when the stored
        value does not match. When omitted the raw object is returned.

    Raises
    ------
    KeyError
        If ``key`` is absent from the context.
    TypeError
        If ``expected_type`` is provided and the stored value does not match the
        requested type.
    """

    value = context[key]
    if expected_type is not None and not isinstance(value, expected_type):
        msg = _type_mismatch_message(key, expected_type, value)
        raise TypeError(msg)
    return value


@overload
def get_optional(context: BehaviorContext, key: str, /) -> Any | None: ...


@overload
def get_optional(
    context: BehaviorContext,
    key: str,
    expected_type: type[T] | tuple[type[T], ...],
    /,
) -> T | None: ...


@overload
def get_optional(
    context: BehaviorContext,
    key: str,
    expected_type: type[T] | tuple[type[T], ...] | None,
    default: T,
    /,
) -> T: ...


def get_optional(
    context: BehaviorContext,
    key: str,
    expected_type: type[T] | tuple[type[T], ...] | None = None,
    default: T | None = None,
) -> Any:
    """Fetch an optional value from ``context`` with an optional type check."""

    if key not in context:
        return default
    value = context[key]
    if expected_type is not None and not isinstance(value, expected_type):
        msg = _type_mismatch_message(key, expected_type, value)
        raise TypeError(msg)
    return value


def get_orchestrator(context: BehaviorContext, key: str = "orchestrator") -> Orchestrator:
    """Retrieve a stored :class:`Orchestrator` instance from ``context``."""

    return get_required(context, key, Orchestrator)


def get_config(context: BehaviorContext, key: str = "config") -> ConfigModel:
    """Retrieve a stored :class:`ConfigModel` instance from ``context``."""

    return get_required(context, key, ConfigModel)


def set_cli_result(
    context: BehaviorContext,
    result: Result,
    *,
    key: str = "cli_result",
) -> Result:
    """Persist a :class:`Result` from a CLI invocation in ``context``."""

    return set_value(context, key, result)


def get_cli_result(
    context: BehaviorContext,
    key: str = "cli_result",
) -> Result:
    """Return a previously stored CLI :class:`Result` from ``context``."""

    return get_required(context, key, Result)


def set_cli_invocation(
    context: BehaviorContext,
    command: Sequence[str],
    result: Result,
    *,
    key: str = "cli_invocation",
) -> CLIInvocation:
    """Capture the command/result pair for later CLI assertions."""

    invocation = CLIInvocation(
        command=tuple(command),
        result=result,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    return set_value(context, key, invocation)


def get_cli_invocation(
    context: BehaviorContext,
    key: str = "cli_invocation",
) -> CLIInvocation:
    """Retrieve a :class:`CLIInvocation` stored via :func:`set_cli_invocation`."""

    return get_required(context, key, CLIInvocation)


def _type_mismatch_message(
    key: str,
    expected_type: type[Any] | tuple[type[Any], ...],
    value: object,
) -> str:
    """Build a helpful ``TypeError`` message for accessor helpers."""

    if isinstance(expected_type, tuple):
        expected = ", ".join(sorted(t.__name__ for t in expected_type))
    else:
        expected = expected_type.__name__
    actual = type(value).__name__
    return f"Value for '{key}' expected ({expected}) but received {actual}"


@dataclass(slots=True)
class CLIInvocation:
    """Capture the outcome of invoking a CLI command within a scenario."""

    command: Sequence[str]
    """Arguments passed to the CLI entrypoint."""

    result: Any
    """Raw runner result to inspect in assertions (e.g., ``CliRunner`` result)."""

    exit_code: int
    """Exit code captured from the invocation."""

    stdout: str
    """Standard output emitted by the CLI."""

    stderr: str | None = None
    """Standard error output when available."""


@dataclass(slots=True)
class APICapture:
    """Describe an HTTP interaction recorded during a scenario."""

    method: str
    """HTTP method used for the request."""

    url: str
    """Target URL for the request."""

    status_code: int
    """HTTP status code returned by the API."""

    json_body: Mapping[str, Any] | None = None
    """JSON response payload when applicable."""

    text_body: str | None = None
    """Fallback textual response body."""

    headers: Mapping[str, str] | None = None
    """Subset of HTTP headers retained for assertions."""


@dataclass(slots=True)
class StreamlitTabMocks:
    """Hold tab mocks returned by :func:`streamlit.tabs`."""

    citations: MagicMock
    """Mock object representing the *Citations* tab."""

    reasoning: MagicMock
    """Mock object representing the *Reasoning* tab."""

    metrics: MagicMock
    """Mock object representing the *Metrics* tab."""

    knowledge_graph: MagicMock
    """Mock object representing the *Knowledge Graph* tab."""

    def as_tuple(self) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
        """Return the stored mocks as a tuple for configuring return values."""

        return (self.citations, self.reasoning, self.metrics, self.knowledge_graph)


@dataclass(slots=True)
class StreamlitComponentMocks:
    """Capture frequently patched Streamlit callables for UI scenarios."""

    markdown: MagicMock
    """Mock for :func:`streamlit.markdown`."""

    tabs: MagicMock
    """Mock for :func:`streamlit.tabs`."""

    container: MagicMock
    """Mock for :func:`streamlit.container`."""

    image: MagicMock
    """Mock for :func:`streamlit.image`."""

    graphviz: MagicMock
    """Mock for :func:`streamlit.graphviz_chart`."""

    success: MagicMock
    """Mock for :func:`streamlit.success`."""

    toggle: MagicMock
    """Mock for :func:`streamlit.toggle`."""

    checkbox: MagicMock
    """Fallback mock for :func:`streamlit.checkbox`."""

    sidebar: MagicMock | None = None
    """Optional mock for :mod:`streamlit.sidebar` utilities."""

    expander: MagicMock | None = None
    """Optional mock for :func:`streamlit.expander`."""


@dataclass(slots=True)
class DesktopRuntimeMocks:
    """Hold patched Qt classes and spy data for desktop UI scenarios."""

    QApplication: type[Any]
    """Instrumented :class:`QApplication` replacement used during tests."""

    AutoresearchMainWindow: type[Any]
    """Instrumented desktop main window exposed to the runtime."""

    apps: list[Any]
    """Instances created from :class:`QApplication`."""

    windows: list[Any]
    """Instances of :class:`AutoresearchMainWindow` constructed during a run."""

    information_calls: list[tuple[str, str]]
    """Calls made to ``QMessageBox.information``."""

    warning_calls: list[tuple[str, str]]
    """Calls made to ``QMessageBox.warning``."""

    critical_calls: list[tuple[str, str]]
    """Calls made to ``QMessageBox.critical``."""

    question_calls: list[tuple[str, str]]
    """Calls made to ``QMessageBox.question``."""

    def latest_window(self) -> Any | None:
        """Return the most recently created desktop window, if any."""

        if self.windows:
            return self.windows[-1]
        return None



@contextmanager
def desktop_runtime(
    monkeypatch: Any, *, exit_code: int = 0
) -> Iterator[DesktopRuntimeMocks]:
    """Patch PySide6 modules with instrumented doubles that call real widgets."""

    import sys
    from threading import Event
    from types import MethodType, SimpleNamespace
    from unittest.mock import MagicMock

    from PySide6 import QtWidgets
    from PySide6.QtWidgets import QMessageBox

    from autoresearch.models import QueryResponse
    from autoresearch.ui.desktop.main_window import (
        AutoresearchMainWindow as _BaseMainWindow,
    )

    created_apps: list[Any] = []
    created_windows: list[Any] = []
    information_calls: list[tuple[str, str]] = []
    warning_calls: list[tuple[str, str]] = []
    critical_calls: list[tuple[str, str]] = []
    question_calls: list[tuple[str, str]] = []

    class InstrumentedQApplication(QtWidgets.QApplication):
        """Record lifecycle events for the QApplication instance."""

        def __init__(self, args: Sequence[str]) -> None:
            super().__init__(list(args))
            self.exec_call_count = 0
            created_apps.append(self)

        def exec(self) -> int:
            self.exec_call_count += 1
            return exit_code

    def information_stub(_parent: Any, title: str, message: str) -> int:
        information_calls.append((title, message))
        return QMessageBox.Ok

    def warning_stub(_parent: Any, title: str, message: str) -> int:
        warning_calls.append((title, message))
        return QMessageBox.Ok

    def critical_stub(_parent: Any, title: str, message: str) -> int:
        critical_calls.append((title, message))
        return QMessageBox.Ok

    class InstrumentedMainWindow(_BaseMainWindow):
        """Autoresearch main window with synchronous helpers for BDD tests."""

        def __init__(self) -> None:
            self.visible = False
            self.events: list[tuple[str, Any]] = []
            self.status_history: list[str] = []
            self.worker_events: list[tuple[str, str]] = []
            self.dialog_log: list[str] = []
            self.pending_failure: tuple[str, str] | None = None
            self._last_result: QueryResponse | None = None
            self._orchestrator_release = Event()
            self._orchestrator_release.set()
            self._result_event = Event()
            self.status_bar_message = "Ready"
            super().__init__()
            created_windows.append(self)
            self.status_history.append(self._status_message)
            self.status_bar_message = self._status_message
            self._install_instrumentation()

        def load_configuration(self) -> None:  # noqa: D401 - documented upstream
            """Load a lightweight configuration and stub orchestrator."""

            self.config = SimpleNamespace(reasoning_mode="balanced", loops=2)
            orchestrator = MagicMock()
            orchestrator.run_query = MagicMock(side_effect=self._orchestrator_run)
            self.orchestrator = orchestrator
            self._set_status_message("Configuration loaded - ready for queries")

        def _install_instrumentation(self) -> None:
            panel = self.query_panel
            if not panel:
                return

            original_set_busy = panel.set_busy
            window_self = self

            def instrumented_set_busy(panel_self: Any, is_busy: bool) -> None:
                original_set_busy(is_busy)
                window_self.events.append(
                    ("controls", "disabled" if is_busy else "enabled")
                )

            panel.set_busy = MethodType(instrumented_set_busy, panel)

        def show(self) -> None:
            self.visible = True
            super().show()

        def _set_status_message(self, message: str) -> None:
            super()._set_status_message(message)
            self.status_bar_message = message
            self.status_history.append(message)

        def _ask_question(self, title: str, message: str, buttons: Any, default: Any) -> Any:
            question_calls.append((title, message))
            self.dialog_log.append("cancel_prompt")
            return QMessageBox.Yes

        def cancel_query(self, session_id: str) -> None:
            self.worker_events.append(("cancel", "requested"))
            super().cancel_query(session_id)

        def _complete_cancellation(self, session_id: Optional[str]) -> None:
            super()._complete_cancellation(session_id)
            self.worker_events.append(("teardown", "complete"))

        def display_results(
            self, result: QueryResponse, session_id: Optional[str] = None
        ) -> None:
            self.events.append(("results", result))
            super().display_results(result, session_id)
            self._last_result = result
            self._result_event.set()

        def display_error(self, error: Exception, session_id: Optional[str] = None) -> None:
            self.events.append(("error", str(error)))
            super().display_error(error, session_id)
            self.worker_events.append(("status_bar", "reset"))

        def submit_query(self, query: str) -> QueryResponse | None:
            panel = self.query_panel
            if not panel or not query.strip():
                return None
            self._result_event.clear()
            panel.set_query_text(query)
            panel.on_run_clicked()
            if not self._orchestrator_release.is_set():
                return None
            if not self._result_event.wait(timeout=5):
                raise TimeoutError("Timed out waiting for orchestrator result")
            self._result_event.clear()
            return self._last_result

        def stage_running_query(self, query: str) -> None:
            self._orchestrator_release.clear()
            self.submit_query(query)

        def set_pending_failure(self, code: str, message: str | None = None) -> None:
            failure_message = message or f"Worker failed: {code}"
            self.pending_failure = (code, failure_message)

        def request_cancel(self) -> None:
            session_id = self._active_session_id or self._resolve_session_id()
            self.cancel_query(session_id)

        def confirm_cancel(self) -> None:
            self.dialog_log.append("cancel_confirmed")

        def resolve_pending_failure(self) -> None:
            self._orchestrator_release.set()

        @property
        def latest_response(self) -> QueryResponse | None:
            return self._last_result

        def _orchestrator_run(self, query: str, _config: Any) -> QueryResponse:
            if not self._orchestrator_release.wait(timeout=5):
                raise TimeoutError("Instrumented orchestrator blocked")
            self._orchestrator_release.set()
            if self.pending_failure is not None:
                _code, message = self.pending_failure
                raise RuntimeError(message)
            return QueryResponse(
                query=query,
                answer=f"Synthesized desktop response for {query}",
                citations=["doc://phase1"],
                reasoning=[f"Desktop orchestrator ran for {query}"],
                metrics={"tokens": 42},
            )

    monkeypatch.setattr(QtWidgets, "QApplication", InstrumentedQApplication)
    monkeypatch.setattr(
        "PySide6.QtWidgets.QApplication", InstrumentedQApplication, raising=False
    )
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", information_stub)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.warning", warning_stub)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.critical", critical_stub)
    monkeypatch.setattr(
        "autoresearch.ui.desktop.main_window.AutoresearchMainWindow",
        InstrumentedMainWindow,
    )

    original_main = sys.modules.pop("autoresearch.ui.desktop.main", None)

    mocks = DesktopRuntimeMocks(
        QApplication=InstrumentedQApplication,
        AutoresearchMainWindow=InstrumentedMainWindow,
        apps=created_apps,
        windows=created_windows,
        information_calls=information_calls,
        warning_calls=warning_calls,
        critical_calls=critical_calls,
        question_calls=question_calls,
    )

    try:
        yield mocks
    finally:
        if original_main is not None:
            sys.modules["autoresearch.ui.desktop.main"] = original_main
        else:
            sys.modules.pop("autoresearch.ui.desktop.main", None)
