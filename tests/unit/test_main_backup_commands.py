import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from autoresearch.main import app
from autoresearch.storage_backup import BackupManager, BackupInfo


@pytest.fixture
def mock_backup_manager():
    """Create a mock BackupManager for testing."""
    mock_manager = MagicMock(spec=BackupManager)
    return mock_manager


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_create_command(mock_backup_manager_class, mock_backup_manager):
    """Test the backup create command."""
    # Setup
    runner = CliRunner()
    mock_backup_manager_class.return_value = mock_backup_manager
    mock_backup_manager.create_backup.return_value = "/path/to/backup.zip"

    # Execute
    result = runner.invoke(
        app, ["backup", "create", "--dir", "test_backups", "--compress"]
    )

    # Verify
    assert result.exit_code == 0
    mock_backup_manager_class.assert_called_once()
    mock_backup_manager.create_backup.assert_called_once()
    assert "Backup created successfully" in result.stdout


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_list_command(mock_backup_manager_class, mock_backup_manager):
    """Test the backup list command."""
    # Setup
    runner = CliRunner()
    mock_backup_manager_class.return_value = mock_backup_manager

    # Create mock backup info objects
    backup1 = BackupInfo(
        path="/path/to/backup1.zip",
        timestamp="2023-01-01 12:00:00",
        size=1024,
        compressed=True,
    )
    backup2 = BackupInfo(
        path="/path/to/backup2.zip",
        timestamp="2023-01-02 12:00:00",
        size=2048,
        compressed=True,
    )

    mock_backup_manager.list_backups.return_value = [backup1, backup2]

    # Execute
    result = runner.invoke(app, ["backup", "list", "--dir", "test_backups"])

    # Verify
    assert result.exit_code == 0
    mock_backup_manager_class.assert_called_once()
    mock_backup_manager.list_backups.assert_called_once()
    assert "Available backups" in result.stdout
    assert "backup1.zip" in result.stdout
    assert "backup2.zip" in result.stdout


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_restore_command(mock_backup_manager_class, mock_backup_manager):
    """Test the backup restore command."""
    # Setup
    runner = CliRunner()
    mock_backup_manager_class.return_value = mock_backup_manager
    mock_backup_manager.restore_backup.return_value = "/path/to/restored"

    # Execute - with force flag to skip confirmation
    result = runner.invoke(app, ["backup", "restore", "/path/to/backup.zip", "--force"])

    # Verify
    assert result.exit_code == 0
    mock_backup_manager_class.assert_called_once()
    mock_backup_manager.restore_backup.assert_called_once_with(
        "/path/to/backup.zip", target_dir=None
    )
    assert "Backup restored successfully" in result.stdout


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_schedule_command(mock_backup_manager_class, mock_backup_manager):
    """Test the backup schedule command."""
    # Setup
    runner = CliRunner()
    mock_backup_manager_class.return_value = mock_backup_manager

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
    mock_backup_manager_class.assert_called_once()
    mock_backup_manager.schedule_backup.assert_called_once()
    assert "Scheduled automatic backups" in result.stdout


@patch("autoresearch.cli_backup.BackupManager")
def test_backup_recover_command(mock_backup_manager_class, mock_backup_manager):
    """Test the backup recover command."""
    # Setup
    runner = CliRunner()
    mock_backup_manager_class.return_value = mock_backup_manager
    mock_backup_manager.point_in_time_recovery.return_value = "/path/to/recovered"

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
    mock_backup_manager_class.assert_called_once()
    mock_backup_manager.point_in_time_recovery.assert_called_once()
    assert "Recovery completed successfully" in result.stdout
