# mypy: ignore-errors
from datetime import datetime

import pytest
from typer.testing import CliRunner

from autoresearch.cli_backup import backup_app, _format_size
from autoresearch.errors import BackupError


pytestmark = pytest.mark.usefixtures("dummy_storage")


class DummyInfo:
    def __init__(self, path="p", ts=None, size=0, compressed=True):
        self.path = path
        self.timestamp = ts or datetime.now()
        self.size = size
        self.compressed = compressed


def test_format_size_units():
    assert _format_size(512) == "512 B"
    assert _format_size(2048).endswith("KB")
    assert _format_size(2 * 1024 * 1024).endswith("MB")
    assert _format_size(3 * 1024 * 1024 * 1024).endswith("GB")


def test_backup_create_error(monkeypatch):
    runner = CliRunner()

    def fail(**_):
        raise BackupError("boom", suggestion="try")

    monkeypatch.setattr("autoresearch.cli_backup.BackupManager.create_backup", fail)
    result = runner.invoke(backup_app, ["create", "--dir", "d"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "boom" in result.stdout
    assert "try" in result.stdout


def test_backup_create_missing_tables(monkeypatch):
    runner = CliRunner()

    def fail(**_):
        raise BackupError("boom", missing_tables=["a", "b"])

    monkeypatch.setattr("autoresearch.cli_backup.BackupManager.create_backup", fail)
    result = runner.invoke(backup_app, ["create", "--dir", "d"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "Missing required tables" in result.stdout
    assert "a, b" in result.stdout


def test_backup_create_success(monkeypatch):
    runner = CliRunner()
    info = DummyInfo(path="p", size=1, compressed=False)
    monkeypatch.setattr(
        "autoresearch.cli_backup.BackupManager.create_backup", lambda **_: info
    )
    result = runner.invoke(backup_app, ["create", "--dir", "d", "--no-compress"])
    assert result.exit_code == 0
    assert "Backup created successfully" in result.stdout


def test_backup_restore_cancelled(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("autoresearch.cli_backup.Prompt.ask", lambda *a, **k: "n")
    result = runner.invoke(backup_app, ["restore", "p"])
    assert "Restore cancelled" in result.stdout


def test_backup_restore_error(monkeypatch):
    runner = CliRunner()

    def fail(**_):
        raise BackupError("oops")

    monkeypatch.setattr("autoresearch.cli_backup.BackupManager.restore_backup", fail)
    monkeypatch.setattr("autoresearch.cli_backup.Prompt.ask", lambda *a, **k: "y")
    result = runner.invoke(backup_app, ["restore", "p"])
    assert result.exit_code == 1
    assert "oops" in result.stdout


def test_backup_list_no_backups(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("autoresearch.cli_backup.BackupManager.list_backups", lambda *_: [])
    result = runner.invoke(backup_app, ["list", "--dir", "d"])
    assert "No backups found" in result.stdout


def test_backup_list_success(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(
        "autoresearch.cli_backup.BackupManager.list_backups",
        lambda *_: [DummyInfo()],
    )
    result = runner.invoke(backup_app, ["list", "--dir", "d"])
    assert result.exit_code == 0
    assert "Backups in d" in result.stdout


def test_backup_recover_invalid_timestamp(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(backup_app, ["recover", "bad"])
    assert result.exit_code == 1
    assert "Invalid timestamp" in result.stdout


def test_backup_recover_error(monkeypatch):
    runner = CliRunner()

    def fail(**_):
        raise BackupError("oops", suggestion="s")

    monkeypatch.setattr("autoresearch.cli_backup.BackupManager.restore_point_in_time", fail)
    monkeypatch.setattr("autoresearch.cli_backup.Prompt.ask", lambda *a, **k: "y")
    result = runner.invoke(backup_app, ["recover", "2020-01-01 00:00:00", "--force"])
    assert result.exit_code == 1
    assert "oops" in result.stdout
    assert "s" in result.stdout
