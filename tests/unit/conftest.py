from typing import Callable

import pytest

from autoresearch.orchestration.orchestrator import Orchestrator


@pytest.fixture
def orchestrator_factory():
    """Return a factory for creating fresh ``Orchestrator`` instances."""

    def _factory() -> Orchestrator:
        return Orchestrator()

    return _factory


@pytest.fixture
def orchestrator(orchestrator_factory: Callable[[], Orchestrator]) -> Orchestrator:
    """Provide a fresh ``Orchestrator`` instance for each test."""

    return orchestrator_factory()
