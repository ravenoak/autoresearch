from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import pytest

from autoresearch import storage_backup
from autoresearch.storage_backup import BackupConfig, BackupInfo, BackupScheduler


@pytest.fixture()
def scheduler_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[BackupScheduler, list[Any], list[tuple[str, str, str, bool, BackupConfig]]]:
    timers: list[Any] = []
    backups: list[tuple[str, str, str, bool, BackupConfig]] = []

    def fake_create_backup(
        *,
        backup_dir: str,
        db_path: str,
        rdf_path: str,
        compress: bool,
        config: BackupConfig | None,
    ) -> BackupInfo:
        assert config is not None
        backups.append((backup_dir, db_path, rdf_path, compress, config))
        return BackupInfo(
            path=f"{backup_dir}/snapshot.tar.gz",
            timestamp=datetime.now(),
            compressed=compress,
            size=1024,
            metadata=None,
        )

    monkeypatch.setattr(storage_backup, "_create_backup", fake_create_backup)

    class DummyTimer:
        def __init__(self, interval: float, callback: Callable[[], None]) -> None:
            self.interval = interval
            self.callback = callback
            self.started = False
            self.cancelled = False
            self.result: Any | None = None

        def start(self) -> None:
            self.started = True
            if self.interval == 0.0:
                self.result = self.callback()
            else:
                self.result = None

        def cancel(self) -> None:
            self.cancelled = True

    def fake_start_timer(interval: float, callback: Callable[[], None]) -> DummyTimer:
        timer = DummyTimer(interval, callback)
        timers.append(timer)
        timer.start()
        return timer

    monkeypatch.setattr(storage_backup, "_start_timer", fake_start_timer)

    scheduler = BackupScheduler()
    yield scheduler, timers, backups
    scheduler.stop()


def test_scheduler_runs_backup_and_reschedules(
    scheduler_environment: tuple[
        BackupScheduler, list[Any], list[tuple[str, str, str, bool, BackupConfig]]
    ],
) -> None:
    scheduler, timers, backups = scheduler_environment

    scheduler.schedule("backups", "kg.duckdb", "kg.rdf", interval_hours=1)

    assert len(backups) == 1
    backup_dir, db_path, rdf_path, compress, config = backups[0]
    assert backup_dir == "backups"
    assert db_path == "kg.duckdb"
    assert rdf_path == "kg.rdf"
    assert compress is True
    assert isinstance(config, BackupConfig)

    assert len(timers) == 2
    assert timers[0].interval == 0.0
    assert timers[0].result is None
    assert timers[1].interval == 3600.0
    assert timers[1].started is True


def test_scheduler_restarts_existing_timer(
    scheduler_environment: tuple[
        BackupScheduler, list[Any], list[tuple[str, str, str, bool, BackupConfig]]
    ],
) -> None:
    scheduler, timers, backups = scheduler_environment

    scheduler.schedule("dir", "db.duckdb", "store.rdf", interval_hours=1)
    previous_timer = timers[-1]

    scheduler.schedule("dir", "db.duckdb", "store.rdf", interval_hours=2)

    assert previous_timer.cancelled is True
    assert len(backups) == 2
    assert timers[-1].interval == 7200.0
