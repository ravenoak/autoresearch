from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from autoresearch.distributed import coordinator as dist_coordinator

from tests.analysis.distributed_coordination_analysis import run


@pytest.fixture
def stub_config() -> SimpleNamespace:
    """Return the minimal configuration objects consumed by the coordinator."""

    return SimpleNamespace(
        storage=SimpleNamespace(duckdb_path="/tmp/autoresearch-test.duckdb"),
        distributed_config=SimpleNamespace(message_broker="memory", broker_url=None),
    )


@pytest.fixture
def stub_brokers(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Provide deterministic broker instances for coordinator orchestration."""

    created: list[StubBroker] = []

    class StubBroker:
        def __init__(self, label: str | None) -> None:
            self.label = label or "memory"
            self.queue = SimpleNamespace(label=f"{self.label}-queue")
            self.published: list[dict[str, Any]] = []

        def publish(self, message: dict[str, Any]) -> None:
            self.published.append(message)

    def fake_get_message_broker(name: str | None, url: str | None = None) -> StubBroker:
        broker = StubBroker(name)
        created.append(broker)
        return broker

    monkeypatch.setattr(dist_coordinator, "get_message_broker", fake_get_message_broker)
    return created


@pytest.fixture
def fake_events(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Replace :func:`multiprocessing.Event` with an in-memory stub."""

    created: list[FakeEvent] = []

    class FakeEvent:
        def __init__(self) -> None:
            self.set_calls = 0
            self.wait_calls = 0
            created.append(self)

        def set(self) -> None:  # pragma: no cover - not exercised in orchestration path
            self.set_calls += 1

        def wait(self) -> None:
            self.wait_calls += 1

    monkeypatch.setattr(dist_coordinator.multiprocessing, "Event", FakeEvent)
    return created


@pytest.fixture
def fake_storage_coordinators(
    monkeypatch: pytest.MonkeyPatch,
) -> list[Any]:
    """Patch :class:`StorageCoordinator` with a lightweight spy."""

    created: list[Any] = []
    original_cls = dist_coordinator.StorageCoordinator

    class RecordingStorageCoordinator(original_cls):
        def __init__(self, queue: Any, db_path: str, ready_event: Any) -> None:
            super().__init__(queue, db_path, ready_event)
            self.start_calls = 0
            created.append(self)

        def start(self) -> None:  # pragma: no cover - behaviour verified via state
            self.start_calls += 1

    monkeypatch.setattr(
        dist_coordinator, "StorageCoordinator", RecordingStorageCoordinator
    )
    return created


@pytest.fixture
def fake_manager(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Replace :func:`multiprocessing.Manager` with an in-memory stub."""

    instances: list[Any] = []

    class FakeManager:
        def __init__(self) -> None:
            self.created_lists: list[list[Any]] = []
            instances.append(self)

        def list(self) -> list[Any]:
            result: list[Any] = []
            self.created_lists.append(result)
            return result

    monkeypatch.setattr(dist_coordinator.multiprocessing, "Manager", FakeManager)
    return instances


@pytest.fixture
def fake_result_aggregators(
    monkeypatch: pytest.MonkeyPatch,
) -> list[Any]:
    """Patch :class:`ResultAggregator` with a lightweight spy."""

    created: list[Any] = []
    original_cls = dist_coordinator.ResultAggregator

    class RecordingResultAggregator(original_cls):
        def __init__(self, queue: Any) -> None:
            super().__init__(queue)
            self.start_calls = 0
            created.append(self)

        def start(self) -> None:  # pragma: no cover - behaviour verified via state
            self.start_calls += 1

    monkeypatch.setattr(dist_coordinator, "ResultAggregator", RecordingResultAggregator)
    return created


def test_distributed_coordination_metrics() -> None:
    metrics = run()
    assert set(metrics) == {1, 2, 4}
    assert all(m["memory_mb"] > 0 for m in metrics.values())


def test_distributed_coordinator_orchestration(
    stub_config: SimpleNamespace,
    stub_brokers: list[Any],
    fake_events: list[Any],
    fake_manager: list[Any],
    fake_storage_coordinators: list[Any],
    fake_result_aggregators: list[Any],
) -> None:
    """Coordinator helpers publish claims and start background workers."""

    coordinator_proc, broker = dist_coordinator.start_storage_coordinator(stub_config)
    assert fake_storage_coordinators, "StorageCoordinator should be instantiated"
    coordinator_instance = fake_storage_coordinators[0]
    assert coordinator_proc is coordinator_instance
    assert coordinator_instance._queue is broker.queue
    assert coordinator_instance._db_path == stub_config.storage.duckdb_path
    assert coordinator_instance.start_calls == 1

    assert fake_events, "Ready event should be created"
    assert fake_events[0].wait_calls == 1

    claim = {"id": "claim-123", "payload": "data"}
    dist_coordinator.publish_claim(broker, claim, partial_update=True)
    assert broker.published == [
        {"action": "persist_claim", "claim": claim, "partial_update": True}
    ]

    aggregator_proc, aggregator_broker = dist_coordinator.start_result_aggregator(
        stub_config
    )
    assert fake_result_aggregators, "ResultAggregator should be instantiated"
    aggregator_instance = fake_result_aggregators[0]
    assert aggregator_proc is aggregator_instance
    assert aggregator_instance._queue is aggregator_broker.queue
    assert aggregator_instance.start_calls == 1

    assert len(stub_brokers) == 2
    assert stub_brokers[0] is broker
    assert stub_brokers[1] is aggregator_broker
