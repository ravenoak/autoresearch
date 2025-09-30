"""Fast tests for storage_backup module."""

from autoresearch.storage_backup import list_backups
from pathlib import Path


def test_list_backups_nonexistent_dir(tmp_path: Path) -> None:
    """Return empty list when backup directory does not exist."""
    missing = tmp_path / "missing"
    backups = list_backups(str(missing))
    assert backups == []
