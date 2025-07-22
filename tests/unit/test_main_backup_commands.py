from datetime import datetime
from typer.testing import CliRunner
from unittest.mock import patch

from autoresearch.main import app
from autoresearch.storage_backup import BackupInfo


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_create_command(mock_manager):
    """Test the backup create command."""
    # Setup
    runner = CliRunner()
    mock_manager.create_backup.return_value = BackupInfo(
        path="/path/to/backup.zip",
        timestamp=datetime.now(),
        compressed=True,
        size=123,
    )

    # Execute
    result = runner.invoke(
        app, ["backup", "create", "--dir", "test_backups", "--compress"]
    )

    # Verify
    assert result.exit_code == 0
    mock_manager.create_backup.assert_called_once()
    assert "Backup created successfully" in result.stdout


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_list_command(mock_manager):
    """Test the backup list command."""
    # Setup
    runner = CliRunner()

    # Create mock backup info objects
    backup1 = BackupInfo(
        path="/path/to/backup1.zip",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        size=1024,
        compressed=True,
    )
    backup2 = BackupInfo(
        path="/path/to/backup2.zip",
        timestamp=datetime(2023, 1, 2, 12, 0, 0),
        size=2048,
        compressed=True,
    )

    mock_manager.list_backups.return_value = [backup1, backup2]

    # Execute
    result = runner.invoke(app, ["backup", "list", "--dir", "test_backups"])

    # Verify
    assert result.exit_code == 0
    mock_manager.list_backups.assert_called_once()
    assert "Backups in test_backups" in result.stdout
    assert "backup1.zip" in result.stdout
    assert "backup2.zip" in result.stdout


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_restore_command(mock_manager):
    """Test the backup restore command."""
    # Setup
    runner = CliRunner()
    mock_manager.restore_backup.return_value = {"db_path": "db", "rdf_path": "rdf"}

    # Execute - with force flag to skip confirmation
    result = runner.invoke(app, ["backup", "restore", "/path/to/backup.zip", "--force"])

    # Verify
    assert result.exit_code == 0
    mock_manager.restore_backup.assert_called_once_with(
        backup_path="/path/to/backup.zip", target_dir=None
    )
    assert "Backup restored successfully" in result.stdout


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_schedule_command(mock_manager):
    """Test the backup schedule command."""
    # Setup
    runner = CliRunner()

    # Execute
    result = runner.invoke(
        app,
        [
            "backup",
            "schedule",
            "--interval",
            "12",
            "--dir",
            "test_backups",
            "--max-backups",
            "3",
            "--retention-days",
            "7",
        ],
    )

    # Verify
    assert result.exit_code == 0
    mock_manager.schedule_backup.assert_called_once()
    assert "Scheduled automatic backups" in result.stdout


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_schedule_command_keyboard_interrupt(mock_manager, monkeypatch):
    """Test stopping the backup schedule with Ctrl+C."""
    runner = CliRunner()

    call = {"count": 0}

    def fake_sleep(_):
        if call["count"] >= 1:
            raise KeyboardInterrupt()
        call["count"] += 1

    monkeypatch.setattr("autoresearch.cli_backup.time.sleep", fake_sleep)

    result = runner.invoke(
        app,
        [
            "backup",
            "schedule",
            "--interval",
            "12",
            "--dir",
            "test_backups",
            "--max-backups",
            "3",
            "--retention-days",
            "7",
        ],
    )

    assert result.exit_code == 0
    mock_manager.schedule_backup.assert_called_once()
    mock_manager.stop_scheduled_backups.assert_called_once()
    assert "Stopping scheduled backups" in result.stdout
    assert "Scheduled backups stopped" in result.stdout


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_recover_command(mock_manager):
    """Test the backup recover command."""
    # Setup
    runner = CliRunner()
    mock_manager.restore_point_in_time.return_value = {
        "db_path": "db",
        "rdf_path": "rdf",
    }

    # Execute - with force flag to skip confirmation
    result = runner.invoke(
        app,
        [
            "backup",
            "recover",
            "2023-01-01 12:00:00",
            "--dir",
            "test_backups",
            "--force",
        ],
    )

    # Verify
    assert result.exit_code == 0
    mock_manager.restore_point_in_time.assert_called_once()
    assert "Point-in-time recovery completed successfully" in result.stdout
