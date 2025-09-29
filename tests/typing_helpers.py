"""Shared typing helpers for pytest fixtures and behavior tests."""

from __future__ import annotations

from collections.abc import Callable, Generator

from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)

from pytest_bdd import given as _given
from pytest_bdd import scenario as _scenario
from pytest_bdd import then as _then
from pytest_bdd import when as _when

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.types import AgentExecutionResult, CallbackMap

if TYPE_CHECKING:
    from autoresearch.orchestration.state import QueryState

R_co = TypeVar("R_co")
T = TypeVar("T")

TypedFixture: TypeAlias = Generator[T, None, None] | T


class StepDecorator(Protocol[R_co]):
    """Protocol for the decorator returned by pytest-bdd step factories."""

    def __call__(self, func: Callable[..., R_co]) -> Callable[..., R_co]: ...


class StepFactory(Protocol[R_co]):
    """Protocol modelling pytest-bdd ``given``/``when``/``then`` factories."""

    @overload
    def __call__(self, func: Callable[..., R_co]) -> Callable[..., R_co]: ...

    @overload
    def __call__(
        self, pattern: Any, /, *args: Any, **kwargs: Any
    ) -> StepDecorator[R_co]: ...


class ScenarioFactory(Protocol):
    """Protocol for the ``pytest_bdd.scenario`` decorator factory."""

    def __call__(
        self, *args: Any, **kwargs: Any
    ) -> StepDecorator[None]: ...


class AgentTestProtocol(Protocol):
    """Protocol capturing the agent surface used within tests."""

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool: ...

    def execute(
        self,
        state: QueryState,
        config: ConfigModel,
        **kwargs: object,
    ) -> AgentExecutionResult: ...


class AgentFactoryProtocol(Protocol):
    """Protocol for factories that resolve agent instances by name."""

    @staticmethod
    def get(name: str, llm_adapter: object | None = None) -> AgentTestProtocol: ...


class QueryRunner(Protocol):
    """Protocol mirroring :meth:`Orchestrator.run_query` call semantics."""

    def __call__(
        self,
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        **kwargs: object,
    ) -> QueryResponse: ...


given = cast("StepFactory[Any]", _given)
when = cast("StepFactory[Any]", _when)
then = cast("StepFactory[Any]", _then)
scenario = cast(ScenarioFactory, _scenario)

__all__ = [
    "TypedFixture",
    "StepDecorator",
    "StepFactory",
    "ScenarioFactory",
    "AgentTestProtocol",
    "AgentFactoryProtocol",
    "QueryRunner",
    "given",
    "when",
    "then",
    "scenario",
]
