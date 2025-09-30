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
    TypedDict,
)

import networkx as nx

from pytest_bdd import given as _given
from pytest_bdd import scenario as _scenario
from pytest_bdd import then as _then
from pytest_bdd import when as _when

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.types import AgentExecutionResult, CallbackMap
from autoresearch.storage import StorageContext

if TYPE_CHECKING:
    from autoresearch.orchestration.state import QueryState
    from autoresearch.storage_backends import DuckDBStorageBackend
    from autoresearch.storage_typing import GraphProtocol

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


class GraphContradictionMetadata(TypedDict):
    raw_score: float
    weighted_score: float
    weight: float
    items: list[dict[str, object]]


class GraphSimilarityMetadata(TypedDict, total=False):
    raw_score: float
    weighted_score: float
    weight: float
    entity_count: float
    relation_count: float


class GraphStageMetadata(TypedDict, total=False):
    contradictions: GraphContradictionMetadata
    similarity: GraphSimilarityMetadata
    neighbors: dict[str, list[dict[str, object]]]
    paths: list[list[str]]


class GraphSummaryMetadata(TypedDict, total=False):
    sources: list[str]
    provenance: list[dict[str, object]]
    relation_count: int
    entity_count: int


class SearchContextGraphAttributes(Protocol):
    """Protocol exposing private graph context attributes for tests."""

    _graph_stage_metadata: GraphStageMetadata
    _graph_summary: GraphSummaryMetadata


def make_storage_context(
    *,
    kg_graph: nx.MultiDiGraph[Any] | None = None,
    db_backend: object | None = None,
    rdf_store: object | None = None,
) -> StorageContext:
    """Return a :class:`StorageContext` populated with typed test doubles."""

    context = StorageContext()
    context.kg_graph = kg_graph
    context.db_backend = cast("DuckDBStorageBackend | None", db_backend)
    context.rdf_store = cast("GraphProtocol | None", rdf_store)
    return context


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
    "GraphStageMetadata",
    "GraphSummaryMetadata",
    "SearchContextGraphAttributes",
    "make_storage_context",
    "given",
    "when",
    "then",
    "scenario",
]
