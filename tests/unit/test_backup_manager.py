"""Tests for storage backup creation, restore, and scheduling."""

from pathlib import Path
import threading

from autoresearch.storage_backup import BackupManager


def test_create_and_restore_backup(tmp_path):
    """BackupManager should create and restore backups correctly."""
    db = tmp_path / "data.db"
    rdf = tmp_path / "store.rdf"
    db.write_text("db")
    rdf.write_text("rdf")
    backup_dir = tmp_path / "backups"

    info = BackupManager.create_backup(
        backup_dir=str(backup_dir),
        db_path=str(db),
        rdf_path=str(rdf),
    )
    assert Path(info.path).exists()

    db.unlink()
    rdf.unlink()
    restore_dir = tmp_path / "restore"
    BackupManager.restore_backup(
        info.path,
        target_dir=str(restore_dir),
        db_filename="data.db",
        rdf_filename="store.rdf",
    )
    assert (restore_dir / "data.db").exists()
    assert (restore_dir / "store.rdf").exists()


def test_backup_scheduler_start_stop(monkeypatch, tmp_path):
    """Scheduled backups should trigger and allow clean shutdown."""
    db = tmp_path / "data.db"
    rdf = tmp_path / "store.rdf"
    db.write_text("db")
    rdf.write_text("rdf")
    called = {}
    done = threading.Event()

    def fake_backup(**kwargs):
        called["invoked"] = True
        done.set()
        return None

    monkeypatch.setattr(
        "autoresearch.storage_backup._create_backup", fake_backup
    )

    scheduler = BackupManager.get_scheduler()
    scheduler.schedule(str(tmp_path / "b"), str(db), str(rdf), interval_hours=1)
    assert done.wait(timeout=1)
    scheduler.stop()
    assert called.get("invoked")
