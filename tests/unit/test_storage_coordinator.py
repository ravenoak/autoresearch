import multiprocessing
from typing import Any

from autoresearch.distributed import StorageCoordinator
from autoresearch import storage
import pytest
from pathlib import Path


class ErrorQueue:
    def get(self):
        raise OSError("fail")


def _noop(*_a, **_k):
    pass


def test_storage_coordinator_persists_message(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    queue: multiprocessing.Queue[Any] = multiprocessing.Queue()
    calls: list[tuple[dict[str, str], bool]] = []

    monkeypatch.setattr(storage, "setup", _noop)
    monkeypatch.setattr(storage, "teardown", _noop)
    monkeypatch.setattr(
        storage.StorageManager,
        "persist_claim",
        lambda claim, partial_update=False: calls.append((claim, partial_update)),
    )

    try:
        coordinator = StorageCoordinator(queue, str(tmp_path / "kg.duckdb"))
        queue.put({"action": "persist_claim", "claim": {"id": "c1"}, "partial_update": True})
        queue.put({"action": "stop"})
        coordinator.run()

        assert calls == [({"id": "c1"}, True)]
    finally:
        queue.close()
        queue.join_thread()


def test_storage_coordinator_handles_stop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    queue: multiprocessing.Queue[Any] = multiprocessing.Queue()
    calls: list[tuple[dict[str, str], bool]] = []

    monkeypatch.setattr(storage, "setup", _noop)
    monkeypatch.setattr(storage, "teardown", _noop)
    monkeypatch.setattr(
        storage.StorageManager,
        "persist_claim",
        lambda claim, partial_update=False: calls.append((claim, partial_update)),
    )

    try:
        coordinator = StorageCoordinator(queue, str(tmp_path / "kg.duckdb"))
        queue.put({"action": "stop"})
        coordinator.run()

        assert calls == []
    finally:
        queue.close()
        queue.join_thread()


def test_storage_coordinator_queue_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "setup", _noop)
    monkeypatch.setattr(storage, "teardown", _noop)

    called = False

    def record_call(*_a, **_k):
        nonlocal called
        called = True

    monkeypatch.setattr(storage.StorageManager, "persist_claim", record_call)

    coordinator = StorageCoordinator(ErrorQueue(), str(tmp_path / "kg.duckdb"))
    coordinator.run()

    assert not called
