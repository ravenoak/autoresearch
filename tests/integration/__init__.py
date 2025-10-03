"""Shared test helpers for integration suites."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pytest import MonkeyPatch

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.types import CallbackMap
from tests.typing_helpers import QueryRunner

QueryResponseFactory = Callable[[str, ConfigModel, CallbackMap | None, dict[str, Any]], QueryResponse]


def configure_api_defaults(
    monkeypatch: MonkeyPatch, *, loops: int = 1
) -> ConfigModel:
    """Return a ``ConfigModel`` with API permissions suitable for tests."""

    ConfigLoader.reset_instance()
    cfg = ConfigModel(loops=loops)
    permissions = cfg.api.role_permissions.setdefault("anonymous", [])
    if "query" not in permissions:
        permissions.append("query")
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


def stub_orchestrator_run_query(
    monkeypatch: MonkeyPatch,
    *,
    response: QueryResponse | QueryResponseFactory | None = None,
) -> QueryRunner:
    """Patch ``Orchestrator.run_query`` with a typed callable for tests."""

    def default_response(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        extra: dict[str, Any] | None = None,
    ) -> QueryResponse:
        return QueryResponse(answer=query, citations=[], reasoning=[], metrics={})

    factory: QueryResponseFactory

    if response is None:

        def default_factory(
            query: str,
            config: ConfigModel,
            callbacks: CallbackMap | None,
            extra: dict[str, Any] | None,
        ) -> QueryResponse:
            return default_response(query, config, callbacks, extra)

        factory = default_factory
    elif isinstance(response, QueryResponse):

        def constant_factory(
            _query: str,
            _config: ConfigModel,
            _callbacks: CallbackMap | None,
            _extra: dict[str, Any] | None,
        ) -> QueryResponse:
            return response

        factory = constant_factory
    else:
        factory = response

    def patched_run_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        **kwargs: Any,
    ) -> QueryResponse:
        return factory(query, config, callbacks, dict(kwargs))

    monkeypatch.setattr(Orchestrator, "run_query", patched_run_query)

    def query_runner(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        **kwargs: Any,
    ) -> QueryResponse:
        return factory(query, config, callbacks, dict(kwargs))

    return query_runner


__all__ = [
    "QueryResponseFactory",
    "configure_api_defaults",
    "stub_orchestrator_run_query",
]
