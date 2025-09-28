"""Shared typing helpers for pytest fixtures and behavior tests."""

from __future__ import annotations

from collections.abc import Callable, Generator
from typing import (
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


given = cast("StepFactory[Any]", _given)
when = cast("StepFactory[Any]", _when)
then = cast("StepFactory[Any]", _then)
scenario = cast(ScenarioFactory, _scenario)

__all__ = [
    "TypedFixture",
    "StepDecorator",
    "StepFactory",
    "ScenarioFactory",
    "given",
    "when",
    "then",
    "scenario",
]
