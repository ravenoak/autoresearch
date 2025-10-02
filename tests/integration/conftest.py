from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, cast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autoresearch.api import app as api_app
from autoresearch.distributed.broker import (
    MessageQueueProtocol,
    StorageBrokerQueueProtocol,
)
from tests.integration._orchestrator_stubs import (
    AgentDouble,
    BrokerQueueStub,
    PersistClaimCall,
    patch_agent_factory_get,
    patch_storage_persist,
    patch_storage_queue,
)
from tests.typing_helpers import TypedFixture

BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "token_baselines.json"
METRIC_BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "backend_metrics.json"
SEARCH_BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "search_baselines.json"


@pytest.fixture
def api_client() -> TypedFixture[TestClient]:
    """Provide a FastAPI TestClient that closes after use."""
    with TestClient(api_app) as client:
        yield client
    return None


@pytest.fixture
def token_baseline(
    request: pytest.FixtureRequest,
) -> TypedFixture[Callable[[dict[str, dict[str, int]], int], None]]:
    """Record and compare token usage across test runs."""

    def _check(tokens: dict[str, dict[str, int]], tolerance: int = 0) -> None:
        data = json.loads(BASELINE_FILE.read_text()) if BASELINE_FILE.exists() else {}
        test_id = request.node.nodeid
        baseline = data.get(test_id)
        if baseline is not None:
            for agent, counts in tokens.items():
                base_counts = baseline.get(agent, {})
                for direction in ("in", "out"):
                    measured = counts.get(direction, 0)
                    expected = base_counts.get(direction, 0)
                    delta = abs(measured - expected)
                    assert (
                        delta <= tolerance
                    ), f"{test_id} {agent} {direction} delta {delta} exceeds tolerance {tolerance}"
        data[test_id] = tokens
        BASELINE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return cast(
        TypedFixture[Callable[[dict[str, dict[str, int]], int], None]],
        _check,
    )


@pytest.fixture
def metrics_baseline(
    request: pytest.FixtureRequest,
) -> TypedFixture[
    Callable[[str, float, float, float, float], None]
]:
    """Record and compare backend metrics across test runs."""

    def _check(
        backend: str,
        precision: float,
        recall: float,
        latency: float,
        tolerance: float = 0.05,
    ) -> None:
        data = json.loads(METRIC_BASELINE_FILE.read_text()) if METRIC_BASELINE_FILE.exists() else {}
        key = f"{request.node.nodeid}::{backend}"
        baseline = data.get(key)
        if baseline is not None:
            assert precision >= baseline["precision"] - tolerance
            assert recall >= baseline["recall"] - tolerance
            assert latency <= baseline["latency"] * (1 + tolerance)
        data[key] = {
            "precision": precision,
            "recall": recall,
            "latency": latency,
        }
        METRIC_BASELINE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return cast(
        TypedFixture[
            Callable[[str, float, float, float, float], None]
        ],
        _check,
    )


@pytest.fixture
def search_baseline(
    request: pytest.FixtureRequest,
) -> TypedFixture[Callable[[Sequence[Mapping[str, object]]], None]]:
    """Record and compare search results across test runs."""

    def _check(results: Sequence[Mapping[str, object]]) -> None:
        data = json.loads(SEARCH_BASELINE_FILE.read_text()) if SEARCH_BASELINE_FILE.exists() else {}
        key = request.node.nodeid
        current = [{"title": r["title"], "url": r["url"]} for r in results]
        baseline = data.get(key)
        if baseline is not None:
            assert current == baseline
        data[key] = current
        SEARCH_BASELINE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return cast(
        TypedFixture[Callable[[Sequence[Mapping[str, object]]], None]],
        _check,
    )


AgentGetter = Callable[[str], AgentDouble]
PersistCallable = Callable[[dict[str, Any], bool], None]
QueuePatcher = Callable[[StorageBrokerQueueProtocol | None], StorageBrokerQueueProtocol]


@pytest.fixture
def stub_agent_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[Callable[[Iterable[AgentDouble]], AgentGetter]]:
    """Return a helper that installs doubles for :class:`AgentFactory`."""

    def _apply(agents: Iterable[AgentDouble]) -> AgentGetter:
        return patch_agent_factory_get(monkeypatch, agents)

    return cast(
        TypedFixture[Callable[[Iterable[AgentDouble]], AgentGetter]],
        _apply,
    )


@pytest.fixture
def stub_storage_persist(
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[Callable[[list[PersistClaimCall] | None], PersistCallable]]:
    """Return a helper that records :func:`StorageManager.persist_claim` calls."""

    def _apply(calls: list[PersistClaimCall] | None = None) -> PersistCallable:
        return patch_storage_persist(monkeypatch, calls)

    return cast(
        TypedFixture[Callable[[list[PersistClaimCall] | None], PersistCallable]],
        _apply,
    )


@pytest.fixture
def stub_storage_queue(
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[QueuePatcher]:
    """Return a helper that injects a :class:`BrokerQueueStub` instance."""

    def _apply(
        queue: StorageBrokerQueueProtocol | None = None,
    ) -> StorageBrokerQueueProtocol:
        stub = patch_storage_queue(monkeypatch, queue)
        queue_view: MessageQueueProtocol = stub
        return cast(StorageBrokerQueueProtocol, queue_view)

    return cast(TypedFixture[QueuePatcher], _apply)
