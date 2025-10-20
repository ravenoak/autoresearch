# mypy: ignore-errors
"""Shared typing helpers for behavior test context payloads."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, MutableMapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace
from typing import Any, TypeVar, overload
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
    """Stubbed :class:`QApplication` replacement used during tests."""

    AutoresearchMainWindow: type[Any]
    """Stubbed desktop main window exposed to the runtime."""

    QMessageBox: type[Any]
    """Stubbed :class:`QMessageBox` replacement capturing dialogs."""

    apps: list[Any]
    """Instances created from :class:`QApplication`."""

    windows: list[Any]
    """Instances of :class:`AutoresearchMainWindow` constructed during a run."""

    message_boxes: list[Any]
    """Dialog instances spawned by the runtime."""

    information_calls: list[tuple[str, str]]
    """Calls made to ``QMessageBox.information``."""

    warning_calls: list[tuple[str, str]]
    """Calls made to ``QMessageBox.warning``."""

    critical_calls: list[tuple[str, str]]
    """Calls made to ``QMessageBox.critical``."""

    qt: Any
    """Simplified :mod:`Qt` namespace exposing required attributes."""

    def latest_window(self) -> Any | None:
        """Return the most recently created desktop window, if any."""

        if self.windows:
            return self.windows[-1]
        return None


@contextmanager
def desktop_runtime(
    monkeypatch: Any, *, exit_code: int = 0
) -> Iterator[DesktopRuntimeMocks]:
    """Patch PySide6 modules with deterministic test doubles.

    Parameters
    ----------
    monkeypatch:
        Active :class:`pytest.MonkeyPatch` fixture.
    exit_code:
        Value returned from the stubbed ``QApplication.exec`` method.
    """

    import sys
    from contextlib import ExitStack

    from autoresearch.models import QueryResponse

    created_apps: list[Any] = []
    created_windows: list[Any] = []
    created_boxes: list[Any] = []
    information_calls: list[tuple[str, str]] = []
    warning_calls: list[tuple[str, str]] = []
    critical_calls: list[tuple[str, str]] = []

    class DummyQApplication:
        """Minimal QApplication stand-in recording lifecycle events."""

        setAttribute = MagicMock()
        setHighDpiScaleFactorRoundingPolicy = MagicMock()

        def __init__(self, args: Sequence[str]) -> None:
            self.args = tuple(args)
            self.setApplicationName = MagicMock()
            self.setApplicationVersion = MagicMock()
            self.setOrganizationName = MagicMock()
            self.exec_call_count = 0
            created_apps.append(self)

        def exec(self) -> int:
            self.exec_call_count += 1
            return exit_code

    class DummyMessageBox:
        """Stub QMessageBox capturing dialog metadata."""

        Critical = "critical"
        Ok = 0

        def __init__(self) -> None:
            self.icon = None
            self.title = None
            self.text = None
            self.detailed_text = None
            self.standard_buttons = None
            created_boxes.append(self)

        def setIcon(self, icon: Any) -> None:  # noqa: N802 - Qt-style API
            self.icon = icon

        def setWindowTitle(self, title: str) -> None:  # noqa: N802 - Qt-style API
            self.title = title

        def setText(self, text: str) -> None:  # noqa: N802 - Qt-style API
            self.text = text

        def setDetailedText(self, text: str) -> None:  # noqa: N802 - Qt-style API
            self.detailed_text = text

        def setStandardButtons(self, buttons: Any) -> None:  # noqa: N802
            self.standard_buttons = buttons

        def exec(self) -> int:  # noqa: A003 - match Qt API
            return 0

        @classmethod
        def information(cls, _parent: Any, title: str, message: str) -> None:
            information_calls.append((title, message))

        @classmethod
        def warning(cls, _parent: Any, title: str, message: str) -> None:
            warning_calls.append((title, message))

        @classmethod
        def critical(cls, _parent: Any, title: str, message: str) -> None:
            critical_calls.append((title, message))

    class StubAutoresearchMainWindow:
        """Simplified desktop window capturing Phase 1 interactions."""

        def __init__(self) -> None:
            from unittest.mock import MagicMock as _MagicMock

            created_windows.append(self)
            self.visible = False
            self.events: list[tuple[str, Any]] = []
            self.submitted_queries: list[str] = []
            self._responses: list[QueryResponse] = []
            self.status_bar_message = "Idle"
            self.status_history: list[str] = [self.status_bar_message]
            self.timer_state = "stopped"
            self.timer_events: list[str] = []
            self.dialog_log: list[str] = []
            self.worker_events: list[tuple[str, str]] = []
            self.pending_failure: tuple[str, str] | None = None
            self.current_query: str | None = None
            self.state = "idle"
            self.orchestrator = _MagicMock()
            self.orchestrator.run_query.side_effect = self._run_query

        def show(self) -> None:
            self.visible = True

        def submit_query(self, query: str) -> QueryResponse | None:
            if not query.strip():
                self.events.append(("warning", "empty"))
                return None
            self.submitted_queries.append(query)
            self.events.append(("controls", "disabled"))
            self._start_running(query)
            try:
                response = self.orchestrator.run_query(query)
            except RuntimeError as error:
                self.events.append(("error", str(error)))
                self._stop_timer()
                self._record_status("Idle")
                self.events.append(("controls", "enabled"))
                return None
            self.events.append(("results", response))
            self._finish_success(response)
            self.events.append(("controls", "enabled"))
            return response

        def stage_running_query(self, query: str) -> None:
            if not query.strip():
                self.events.append(("warning", "empty"))
                return
            self.submitted_queries.append(query)
            self.events.append(("controls", "disabled"))
            self._start_running(query)
            self.pending_failure = None

        def set_pending_failure(self, code: str, message: str | None = None) -> None:
            failure_message = message or f"Worker failed: {code}"
            self.pending_failure = (code, failure_message)

        def request_cancel(self) -> None:
            self.dialog_log.append("cancel_prompt")
            DummyMessageBox.warning(
                None,
                "Cancel query?",
                "Cancel the active desktop query?",
            )

        def confirm_cancel(self) -> None:
            self.dialog_log.append("cancel_confirmed")
            self.worker_events.append(("cancel", "requested"))
            self.state = "cancelling"
            self._stop_timer()
            self._record_status("Cancelling")

        def resolve_pending_failure(self) -> None:
            if self.pending_failure is None:
                return
            code, message = self.pending_failure
            DummyMessageBox.critical(None, "Query failed", message)
            self.events.append(("error", code))
            self.worker_events.append(("teardown", "complete"))
            self.worker_events.append(("status_bar", "reset"))
            self.pending_failure = None
            self._stop_timer()
            self._record_status("Idle")
            self.events.append(("controls", "enabled"))
            self.state = "failed"

        def _run_query(self, query: str) -> QueryResponse:
            if self.pending_failure is not None:
                code, _ = self.pending_failure
                raise RuntimeError(code)
            response = QueryResponse(
                query=query,
                answer=f"Synthesized desktop response for {query}",
                citations=["doc://phase1"],
                reasoning=[f"Desktop orchestrator ran for {query}"],
                metrics={"tokens": 42},
            )
            return response

        def _start_running(self, query: str) -> None:
            self.state = "running"
            self.current_query = query
            self.timer_state = "running"
            self.timer_events.append("started")
            self.events.append(("timer", "started"))
            self._record_status("Running")

        def _finish_success(self, response: QueryResponse) -> QueryResponse:
            self._responses.append(response)
            self._stop_timer()
            self._record_status("Idle")
            self.state = "idle"
            return response

        def _stop_timer(self) -> None:
            if self.timer_state == "running":
                self.timer_state = "stopped"
                self.timer_events.append("stopped")
                self.events.append(("timer", "stopped"))

        def _record_status(self, label: str) -> None:
            self.status_bar_message = label
            self.status_history.append(label)
            self.events.append(("status", label.lower()))

        @property
        def latest_response(self) -> QueryResponse | None:
            if self._responses:
                return self._responses[-1]
            return None

    qt_namespace = SimpleNamespace(
        ApplicationAttribute=SimpleNamespace(AA_EnableHighDpiScaling="AA_EnableHighDpiScaling"),
        HighDpiScaleFactorRoundingPolicy=SimpleNamespace(PassThrough="PassThrough"),
    )

    qtcore_module = ModuleType("PySide6.QtCore")
    qtcore_module.Qt = qt_namespace

    qtwidgets_module = ModuleType("PySide6.QtWidgets")
    qtwidgets_module.QApplication = DummyQApplication
    qtwidgets_module.QMessageBox = DummyMessageBox

    pyside6_module = ModuleType("PySide6")
    pyside6_module.QtCore = qtcore_module
    pyside6_module.QtWidgets = qtwidgets_module

    main_window_module = ModuleType("autoresearch.ui.desktop.main_window")
    main_window_module.AutoresearchMainWindow = StubAutoresearchMainWindow

    patched_modules = {
        "PySide6": pyside6_module,
        "PySide6.QtCore": qtcore_module,
        "PySide6.QtWidgets": qtwidgets_module,
        "autoresearch.ui.desktop.main_window": main_window_module,
    }

    original_modules: dict[str, ModuleType | None] = {}

    with ExitStack() as stack:
        for name, module in patched_modules.items():
            original_modules[name] = sys.modules.get(name)
            stack.callback(
                lambda n=name, original=original_modules[name]: _restore_module(n, original)
            )
            sys.modules[name] = module

        original_main = sys.modules.pop("autoresearch.ui.desktop.main", None)
        stack.callback(lambda: _restore_module("autoresearch.ui.desktop.main", original_main))

        monkeypatch.setenv("AUTORESEARCH_SUPPRESS_DIALOGS", "1")

        mocks = DesktopRuntimeMocks(
            QApplication=DummyQApplication,
            AutoresearchMainWindow=StubAutoresearchMainWindow,
            QMessageBox=DummyMessageBox,
            apps=created_apps,
            windows=created_windows,
            message_boxes=created_boxes,
            information_calls=information_calls,
            warning_calls=warning_calls,
            critical_calls=critical_calls,
            qt=qt_namespace,
        )

        try:
            yield mocks
        finally:
            stack.close()


def _restore_module(name: str, module: ModuleType | None) -> None:
    """Return ``sys.modules[name]`` to its original value."""

    import sys

    if module is None:
        sys.modules.pop(name, None)
    else:
        sys.modules[name] = module
