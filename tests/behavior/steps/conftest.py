"""Shared fixtures for behavior step modules."""

from __future__ import annotations

import pytest

from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.types import CallbackMap
from autoresearch.storage import StorageManager
from tests.behavior.context import (
    BehaviorContext,
    get_config,
    get_orchestrator,
    set_value,
)
from tests.typing_helpers import TypedFixture


@pytest.fixture(autouse=True)
def orchestrator_context(
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[None]:
    """Provide a shared orchestrator and baseline config for step implementations."""

    orchestrator = Orchestrator()
    config = ConfigModel()
    set_value(bdd_context, "orchestrator", orchestrator)
    set_value(bdd_context, "config", config)

    # Assert the context exposes typed instances before any steps execute.
    assert get_orchestrator(bdd_context) is orchestrator
    assert get_config(bdd_context) is config

    original_run_query = Orchestrator.run_query

    def run_query_wrapper(
        query: str,
        config_model: ConfigModel,
        callbacks: CallbackMap | None = None,
        *,
        agent_factory: type[AgentFactory] = AgentFactory,
        storage_manager: type[StorageManager] = StorageManager,
        visualize: bool = False,
    ) -> object:
        return original_run_query(
            orchestrator,
            query,
            config_model,
            callbacks,
            agent_factory=agent_factory,
            storage_manager=storage_manager,
            visualize=visualize,
        )

    monkeypatch.setattr(Orchestrator, "run_query", staticmethod(run_query_wrapper))
    monkeypatch.setattr(Orchestrator, "_orig_run_query", original_run_query, raising=False)
    yield None
    return None
