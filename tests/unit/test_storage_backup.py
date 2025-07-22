"""Unit tests for the storage backup and restore functionality.

This module tests the backup and restore functionality for the storage system,
including scheduled backups, rotation policies, compression, and point-in-time recovery.
"""

import os
import shutil
import tempfile
from unittest.mock import patch
import pytest
import duckdb
import rdflib

from autoresearch.storage_backup import (
    BackupManager,
    create_backup,
    restore_backup,
    list_backups,
    schedule_backup,
    BackupConfig,
)
from autoresearch.errors import BackupError

pytestmark = pytest.mark.slow


@pytest.fixture
def temp_dir():
    """Create a temporary directory for backups."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_storage(temp_dir):
    """Set up a mock storage system with test data."""
    # Create a test DuckDB database
    db_path = os.path.join(temp_dir, "test.duckdb")
    conn = duckdb.connect(db_path)

    # Create test tables
    conn.execute("CREATE TABLE test_table (id INTEGER, name VARCHAR)")
    conn.execute("INSERT INTO test_table VALUES (1, 'Test 1'), (2, 'Test 2')")

    # Create a test RDF store
    rdf_path = os.path.join(temp_dir, "test.rdf")
    g = rdflib.Graph()
    g.add(
        (
            rdflib.URIRef("http://example.org/subject"),
            rdflib.URIRef("http://example.org/predicate"),
            rdflib.Literal("Test object"),
        )
    )
    g.serialize(destination=rdf_path, format="turtle")

    # Mock the StorageManager to use these test files
    with (
        patch("autoresearch.storage._db_backend") as mock_db_backend,
        patch("autoresearch.storage._rdf_store") as mock_rdf_store,
    ):
        mock_db_backend._path = db_path
        mock_db_backend.get_connection.return_value = conn

        mock_rdf_store.serialize.return_value = g.serialize(format="turtle")

        yield {"db_path": db_path, "rdf_path": rdf_path, "conn": conn, "graph": g}

    # Clean up
    conn.close()


def test_create_backup_basic(mock_storage, temp_dir):
    """Test creating a basic backup without compression."""
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Create a backup
    backup_info = create_backup(
        backup_dir=backup_dir,
        db_path=mock_storage["db_path"],
        rdf_path=mock_storage["rdf_path"],
        compress=False,
    )

    # Verify backup was created
    assert os.path.exists(backup_info.path)
    assert os.path.exists(os.path.join(backup_info.path, "db.duckdb"))
    assert os.path.exists(os.path.join(backup_info.path, "store.rdf"))

    # Verify backup info
    assert backup_info.timestamp is not None
    assert not backup_info.compressed
    assert backup_info.size > 0


def test_create_backup_with_compression(mock_storage, temp_dir):
    """Test creating a backup with compression."""
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Create a backup with compression
    backup_info = create_backup(
        backup_dir=backup_dir,
        db_path=mock_storage["db_path"],
        rdf_path=mock_storage["rdf_path"],
        compress=True,
    )

    # Verify backup was created
    assert os.path.exists(backup_info.path)
    assert backup_info.path.endswith(".tar.gz")

    # Verify backup info
    assert backup_info.timestamp is not None
    assert backup_info.compressed
    assert backup_info.size > 0


def test_restore_backup_basic(mock_storage, temp_dir):
    """Test restoring a basic backup without compression."""
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Create a backup
    backup_info = create_backup(
        backup_dir=backup_dir,
        db_path=mock_storage["db_path"],
        rdf_path=mock_storage["rdf_path"],
        compress=False,
    )

    # Modify the original data
    mock_storage["conn"].execute("DELETE FROM test_table")

    # Create a new destination directory
    restore_dir = os.path.join(temp_dir, "restore")
    os.makedirs(restore_dir, exist_ok=True)

    # Restore the backup
    restored_paths = restore_backup(
        backup_path=backup_info.path, target_dir=restore_dir
    )

    # Verify restored files exist
    assert os.path.exists(restored_paths["db_path"])
    assert os.path.exists(restored_paths["rdf_path"])

    # Verify the restored file exists and has content
    assert os.path.getsize(restored_paths["db_path"]) > 0

    # For a more thorough test, we would need to initialize the database
    # and verify the schema and data, but that's beyond the scope of this test


def test_restore_backup_with_compression(mock_storage, temp_dir):
    """Test restoring a backup with compression."""
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Create a backup with compression
    backup_info = create_backup(
        backup_dir=backup_dir,
        db_path=mock_storage["db_path"],
        rdf_path=mock_storage["rdf_path"],
        compress=True,
    )

    # Create a new destination directory
    restore_dir = os.path.join(temp_dir, "restore")
    os.makedirs(restore_dir, exist_ok=True)

    # Restore the backup
    restored_paths = restore_backup(
        backup_path=backup_info.path, target_dir=restore_dir
    )

    # Verify restored files exist
    assert os.path.exists(restored_paths["db_path"])
    assert os.path.exists(restored_paths["rdf_path"])


def test_list_backups(mock_storage, temp_dir):
    """Test listing available backups."""
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Create multiple backups
    backup1 = create_backup(
        backup_dir=backup_dir,
        db_path=mock_storage["db_path"],
        rdf_path=mock_storage["rdf_path"],
        compress=False,
    )

    # Wait a moment to ensure different timestamps
    import time

    time.sleep(1)

    backup2 = create_backup(
        backup_dir=backup_dir,
        db_path=mock_storage["db_path"],
        rdf_path=mock_storage["rdf_path"],
        compress=True,
    )

    # List backups
    backups = list_backups(backup_dir)

    # Verify backups are listed correctly
    assert len(backups) == 2
    assert any(b.path == backup1.path for b in backups)
    assert any(b.path == backup2.path for b in backups)

    # Verify backups are sorted by timestamp (newest first)
    assert backups[0].timestamp > backups[1].timestamp


def test_backup_rotation_policy(mock_storage, temp_dir):
    """Test backup rotation policy."""
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Create a backup config with rotation policy
    config = BackupConfig(
        backup_dir=backup_dir, compress=True, max_backups=2, retention_days=30
    )

    # Create multiple backups
    for i in range(3):
        create_backup(
            backup_dir=backup_dir,
            db_path=mock_storage["db_path"],
            rdf_path=mock_storage["rdf_path"],
            compress=True,
            config=config,
        )
        # Wait a moment to ensure different timestamps
        import time

        time.sleep(1)

    # List backups
    backups = list_backups(backup_dir)

    # Verify only the most recent 2 backups are kept
    assert len(backups) == 2


def test_scheduled_backup(mock_storage, temp_dir):
    """Test scheduled backup functionality."""
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Mock the scheduler
    with patch("autoresearch.storage_backup.BackupScheduler") as mock_scheduler:
        # Configure scheduled backup
        schedule_backup(
            backup_dir=backup_dir,
            db_path=mock_storage["db_path"],
            rdf_path=mock_storage["rdf_path"],
            interval_hours=24,
            compress=True,
            max_backups=5,
        )

        # Verify scheduler was called with correct parameters
        mock_scheduler.assert_called_once()
        mock_scheduler.return_value.schedule.assert_called_once()
        args, kwargs = mock_scheduler.return_value.schedule.call_args
        assert kwargs["interval_hours"] == 24
        assert kwargs["compress"] is True
        assert kwargs["max_backups"] == 5


def test_point_in_time_recovery(mock_storage, temp_dir):
    """Test point-in-time recovery functionality."""
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Create multiple backups with different timestamps
    backup_times = []

    for i in range(3):
        # Create a backup
        backup_info = create_backup(
            backup_dir=backup_dir,
            db_path=mock_storage["db_path"],
            rdf_path=mock_storage["rdf_path"],
            compress=False,
        )
        backup_times.append(backup_info.timestamp)

        # Modify the data for the next backup
        mock_storage["conn"].execute(
            f"INSERT INTO test_table VALUES ({i + 3}, 'Test {i + 3}')"
        )

        # Wait a moment to ensure different timestamps
        import time

        time.sleep(1)

    # Restore to a point in time (the second backup)
    target_time = backup_times[1]

    restore_dir = os.path.join(temp_dir, "restore_pit")
    os.makedirs(restore_dir, exist_ok=True)

    # Perform point-in-time recovery
    restored_paths = BackupManager.restore_point_in_time(
        backup_dir=backup_dir, target_time=target_time, target_dir=restore_dir
    )

    # Verify restored files exist
    assert os.path.exists(restored_paths["db_path"])
    assert os.path.exists(restored_paths["rdf_path"])

    # Verify the restored file exists and has content
    assert os.path.getsize(restored_paths["db_path"]) > 0

    # For a more thorough test, we would need to initialize the database
    # and verify the schema and data, but that's beyond the scope of this test


def test_backup_error_handling(mock_storage, temp_dir):
    """Test error handling during backup operations."""
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Test with invalid paths
    with pytest.raises(BackupError):
        create_backup(
            backup_dir=backup_dir,
            db_path="/nonexistent/path.duckdb",
            rdf_path=mock_storage["rdf_path"],
            compress=False,
        )

    # Test with invalid backup path during restore
    with pytest.raises(BackupError):
        restore_backup(
            backup_path="/nonexistent/backup",
            target_dir=os.path.join(temp_dir, "restore"),
        )
