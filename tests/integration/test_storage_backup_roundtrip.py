"""Integration test for backup and restore using real files."""

from pathlib import Path

from autoresearch.storage_backup import BackupManager


def test_backup_roundtrip(tmp_path):
    """BackupManager can create and restore backups on disk."""
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
