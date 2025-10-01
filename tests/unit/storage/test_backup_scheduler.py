from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import pytest

from autoresearch import storage_backup
from autoresearch.storage_backup import (
    BackupConfig,
    BackupInfo,
    BackupManager,
    BackupScheduler,
)


@pytest.fixture()
def scheduler_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[BackupScheduler, list["DummyTimer"], list[tuple[str, str, str, bool, BackupConfig]]]:
    timers: list[DummyTimer] = []
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
        BackupScheduler, list["DummyTimer"], list[tuple[str, str, str, bool, BackupConfig]]
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
        BackupScheduler, list["DummyTimer"], list[tuple[str, str, str, bool, BackupConfig]]
    ],
) -> None:
    scheduler, timers, backups = scheduler_environment

    scheduler.schedule("dir", "db.duckdb", "store.rdf", interval_hours=1)
    previous_timer = timers[-1]

    scheduler.schedule("dir", "db.duckdb", "store.rdf", interval_hours=2)

    assert previous_timer.cancelled is True
    assert len(backups) == 2
    assert timers[-1].interval == 7200.0


def test_backup_manager_schedule_uses_resolved_scheduler(
    scheduler_environment: tuple[
        BackupScheduler, list["DummyTimer"], list[tuple[str, str, str, bool, BackupConfig]]
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scheduler, timers, backups = scheduler_environment

    monkeypatch.setattr(BackupManager, "_scheduler", scheduler)
    try:
        BackupManager.schedule_backup(
            backup_dir="backups",
            db_path="kg.duckdb",
            rdf_path="kg.rdf",
            interval_hours=3,
            compress=False,
            max_backups=2,
            retention_days=7,
        )
        assert len(backups) == 1
        _, _, _, compress, config = backups[0]
        assert compress is False
        assert config.max_backups == 2
        assert config.retention_days == 7
        assert len(timers) == 2
        assert timers[0].interval == 0.0
        assert timers[1].interval == pytest.approx(10800.0)
    finally:
        BackupManager._scheduler = None


def test_rotation_policy_removes_excess_and_stale_backups(tmp_path: Path) -> None:
    """Rotation deletes old backups while keeping the newest ones."""

    config = BackupConfig(backup_dir=str(tmp_path), max_backups=2, retention_days=1)
    now = datetime.now()
    layout = [
        (now - timedelta(minutes=10), True),
        (now - timedelta(hours=1), True),
        (now - timedelta(hours=5), False),
        (now - timedelta(days=2), True),
    ]

    for timestamp, compressed in layout:
        stem = timestamp.strftime("%Y%m%d_%H%M%S")
        if compressed:
            path = tmp_path / f"backup_{stem}.tar.gz"
            path.write_bytes(b"data")
        else:
            directory = tmp_path / f"backup_{stem}"
            directory.mkdir()
            (directory / "db.duckdb").write_text("data")

    storage_backup._apply_rotation_policy(str(tmp_path), config)

    remaining = {item.name for item in tmp_path.iterdir()}
    recent_key = (now - timedelta(minutes=10)).strftime("%Y%m%d_%H%M%S")
    hourly_key = (now - timedelta(hours=1)).strftime("%Y%m%d_%H%M%S")
    expected = {
        f"backup_{recent_key}.tar.gz",
        f"backup_{hourly_key}.tar.gz",
    }
    assert remaining == expected
