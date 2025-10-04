"""Shared typing helpers for behavior test context payloads."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar, overload
from unittest.mock import MagicMock

from click.testing import Result

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator

__all__ = [
    "APICapture",
    "BehaviorContext",
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
def get_required(context: BehaviorContext, key: str, /) -> Any:
    ...


@overload
def get_required(
    context: BehaviorContext,
    key: str,
    expected_type: type[T] | tuple[type[T], ...],
    /,
) -> T:
    ...


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
def get_optional(context: BehaviorContext, key: str, /) -> Any | None:
    ...


@overload
def get_optional(
    context: BehaviorContext,
    key: str,
    expected_type: type[T] | tuple[type[T], ...],
    /,
) -> T | None:
    ...


@overload
def get_optional(
    context: BehaviorContext,
    key: str,
    expected_type: type[T] | tuple[type[T], ...] | None,
    default: T,
    /,
) -> T:
    ...


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

