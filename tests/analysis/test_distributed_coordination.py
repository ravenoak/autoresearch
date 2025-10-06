from __future__ import annotations

import multiprocessing
from pathlib import Path
from multiprocessing.managers import ListProxy
from typing import Any, cast

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.distributed import coordinator as dist_coordinator
from autoresearch.distributed.broker import AgentResultMessage

from tests.analysis.distributed_coordination_analysis import run
from tests.typing_helpers import TypedFixture


class StubQueue:
    """Minimal queue stub capturing metadata for assertions."""

    def __init__(self, label: str) -> None:
        self.label = label


class StubBroker:
    """Lightweight broker capturing published messages."""

    def __init__(self, label: str | None) -> None:
        self.label = label or "memory"
        self.queue = StubQueue(label=f"{self.label}-queue")
        self.published: list[dict[str, Any]] = []

    def publish(self, message: dict[str, Any]) -> None:
        self.published.append(message)


class RecordedEvent:
    """Simple stand-in for :class:`multiprocessing.Event`."""

    def __init__(self) -> None:
        self.set_calls = 0
        self.wait_calls = 0

    def set(self) -> None:  # pragma: no cover - behaviour inspected via counters
        self.set_calls += 1

    def wait(self) -> bool:
        self.wait_calls += 1
        return True


@pytest.fixture
def stub_config(tmp_path: Path) -> TypedFixture[ConfigModel]:
    """Return a concrete :class:`ConfigModel` tailored for coordinator tests."""

    config = ConfigModel()
    config.storage.duckdb_path = str(tmp_path / "autoresearch-test.duckdb")
    config.distributed_config.message_broker = "memory"
    config.distributed_config.broker_url = None
    return config


@pytest.fixture
def stub_brokers(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[list[StubBroker]]:
    """Provide deterministic broker instances for coordinator orchestration."""

    created: list[StubBroker] = []

    def fake_get_message_broker(name: str | None, url: str | None = None) -> StubBroker:
        broker = StubBroker(name)
        created.append(broker)
        return broker

    monkeypatch.setattr(dist_coordinator, "get_message_broker", fake_get_message_broker)
    return created


@pytest.fixture
def fake_events(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[list[RecordedEvent]]:
    """Replace :func:`multiprocessing.Event` with an in-memory stub."""

    created: list[RecordedEvent] = []

    def factory(*_: Any, **__: Any) -> RecordedEvent:
        event = RecordedEvent()
        created.append(event)
        return event

    module_multiprocessing = cast(Any, dist_coordinator).multiprocessing
    monkeypatch.setattr(module_multiprocessing, "Event", factory)
    return created


@pytest.fixture
def fake_storage_coordinators(
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[list[dist_coordinator.StorageCoordinator]]:
    """Patch :class:`StorageCoordinator` with a lightweight spy."""

    created: list[dist_coordinator.StorageCoordinator] = []

    class RecordingStorageCoordinator(dist_coordinator.StorageCoordinator):
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
def fake_result_aggregators(
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[list[dist_coordinator.ResultAggregator]]:
    """Patch :class:`ResultAggregator` with a lightweight spy."""

    created: list[dist_coordinator.ResultAggregator] = []

    class RecordingResultAggregator(dist_coordinator.ResultAggregator):
        def __init__(self, queue: Any) -> None:
            multiprocessing.Process.__init__(self, daemon=True)
            self._queue = queue
            self.results = cast("ListProxy[AgentResultMessage]", [])
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
    stub_config: ConfigModel,
    stub_brokers: list[StubBroker],
    fake_events: list[RecordedEvent],
    fake_storage_coordinators: list[dist_coordinator.StorageCoordinator],
    fake_result_aggregators: list[dist_coordinator.ResultAggregator],
) -> None:
    """Coordinator helpers publish claims and start background workers."""

    config = stub_config
    coordinator_proc, broker = dist_coordinator.start_storage_coordinator(config)
    assert isinstance(broker, StubBroker)
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

    aggregator_proc, aggregator_broker = dist_coordinator.start_result_aggregator(config)
    assert fake_result_aggregators, "ResultAggregator should be instantiated"
    aggregator_instance = fake_result_aggregators[0]
    assert aggregator_proc is aggregator_instance
    assert isinstance(aggregator_broker, StubBroker)
    assert aggregator_instance._queue is aggregator_broker.queue
    assert aggregator_instance.start_calls == 1

    assert len(stub_brokers) == 2
    assert stub_brokers[0] is broker
    assert stub_brokers[1] is aggregator_broker
