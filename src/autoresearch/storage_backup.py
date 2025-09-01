"""Storage backup and restore functionality for the Autoresearch project.

This module provides functionality for backing up and restoring the storage system,
including scheduled backups, rotation policies, compression, and point-in-time recovery.
"""

import os
import shutil
import tarfile
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .errors import BackupError
from .logging_utils import get_logger
from .config import ConfigLoader

log = get_logger(__name__)


@dataclass
class BackupInfo:
    """Information about a backup."""

    path: str
    timestamp: datetime
    compressed: bool
    size: int
    metadata: Dict[str, Any] | None = None


@dataclass
class BackupConfig:
    """Configuration for backup operations."""

    backup_dir: str
    compress: bool = True
    max_backups: int = 5
    retention_days: int = 30


def _create_backup(
    backup_dir: str,
    db_path: str,
    rdf_path: str,
    compress: bool = True,
    config: Optional[BackupConfig] = None,
) -> BackupInfo:
    """Create a backup of the storage system.

    Args:
        backup_dir: Directory where backups will be stored
        db_path: Path to the DuckDB database file
        rdf_path: Path to the RDF store file or directory
        compress: Whether to compress the backup
        config: Additional configuration for backup operations

    Returns:
        Information about the created backup

    Raises:
        BackupError: If the backup operation fails
    """
    try:
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)

        # Generate timestamp for backup
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

        # Create backup path
        if compress:
            backup_path = os.path.join(backup_dir, f"backup_{timestamp_str}.tar.gz")
        else:
            backup_path = os.path.join(backup_dir, f"backup_{timestamp_str}")
            os.makedirs(backup_path, exist_ok=True)

        # Copy files to backup location
        if compress:
            with tarfile.open(backup_path, "w:gz") as tar:
                # Add DuckDB file
                if os.path.exists(db_path):
                    tar.add(db_path, arcname="db.duckdb")
                else:
                    raise BackupError(f"DuckDB file not found: {db_path}")

                # Add RDF store
                if os.path.exists(rdf_path):
                    if os.path.isdir(rdf_path):
                        # If it's a directory, add all files
                        for root, _, files in os.walk(rdf_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.join(
                                    "store.rdf", os.path.relpath(file_path, rdf_path)
                                )
                                tar.add(file_path, arcname=arcname)
                    else:
                        # If it's a file, add it directly
                        tar.add(rdf_path, arcname="store.rdf")
                else:
                    raise BackupError(f"RDF store not found: {rdf_path}")
        else:
            # Copy DuckDB file
            if os.path.exists(db_path):
                shutil.copy2(db_path, os.path.join(backup_path, "db.duckdb"))
            else:
                raise BackupError(f"DuckDB file not found: {db_path}")

            # Copy RDF store
            if os.path.exists(rdf_path):
                if os.path.isdir(rdf_path):
                    # If it's a directory, copy the whole directory
                    shutil.copytree(
                        rdf_path,
                        os.path.join(backup_path, "store.rdf"),
                        dirs_exist_ok=True,
                    )
                else:
                    # If it's a file, copy it directly
                    shutil.copy2(rdf_path, os.path.join(backup_path, "store.rdf"))
            else:
                raise BackupError(f"RDF store not found: {rdf_path}")

        # Get backup size
        if compress:
            size = os.path.getsize(backup_path)
        else:
            size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(backup_path)
                for filename in filenames
            )

        # Create backup info
        backup_info = BackupInfo(
            path=backup_path,
            timestamp=timestamp,
            compressed=compress,
            size=size,
            metadata={
                "db_path": db_path,
                "rdf_path": rdf_path,
            },
        )

        log.info(
            f"Created backup at {backup_path} "
            f"({'compressed' if compress else 'uncompressed'}, {size} bytes)"
        )

        # Apply rotation policy if configured
        if config:
            _apply_rotation_policy(backup_dir, config)

        return backup_info

    except Exception as e:
        log.error(f"Backup failed: {e}")
        raise BackupError(f"Failed to create backup: {e}")


def _restore_backup(
    backup_path: str,
    target_dir: str,
    db_filename: str = "db.duckdb",
    rdf_filename: str = "store.rdf",
) -> Dict[str, str]:
    """Restore a backup to the specified directory.

    Args:
        backup_path: Path to the backup to restore
        target_dir: Directory where the backup will be restored
        db_filename: Filename for the restored DuckDB database
        rdf_filename: Filename for the restored RDF store

    Returns:
        Dictionary with paths to the restored files

    Raises:
        BackupError: If the restore operation fails
    """
    try:
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Determine if the backup is compressed
        is_compressed = backup_path.endswith(".tar.gz") or backup_path.endswith(".tgz")

        # Paths for restored files
        db_target_path = os.path.join(target_dir, db_filename)
        rdf_target_path = os.path.join(target_dir, rdf_filename)

        # Restore from compressed backup
        if is_compressed:
            if not os.path.exists(backup_path):
                raise BackupError(f"Backup file not found: {backup_path}")

            try:
                with tarfile.open(backup_path, "r:gz") as tar:
                    # Extract DuckDB file
                    try:
                        db_member = tar.getmember("db.duckdb")
                        db_file = tar.extractfile(db_member)
                        if db_file:
                            with open(db_target_path, "wb") as f:
                                f.write(db_file.read())
                    except KeyError:
                        raise BackupError("DuckDB file not found in backup")

                    # Extract RDF store
                    try:
                        # Check if store.rdf is a file or directory in the archive
                        rdf_members = [
                            m for m in tar.getmembers() if m.name.startswith("store.rdf")
                        ]
                        if not rdf_members:
                            raise BackupError("RDF store not found in backup")

                        if (
                            len(rdf_members) == 1
                            and rdf_members[0].name == "store.rdf"
                            and not rdf_members[0].isdir()
                        ):
                            # It's a single file
                            rdf_file = tar.extractfile(rdf_members[0])
                            if rdf_file:
                                with open(rdf_target_path, "wb") as f:
                                    f.write(rdf_file.read())
                        else:
                            # It's a directory
                            os.makedirs(rdf_target_path, exist_ok=True)
                            for member in rdf_members:
                                if member.name != "store.rdf":  # Skip the directory itself
                                    # Extract to the target directory
                                    member_path = os.path.join(
                                        rdf_target_path,
                                        os.path.relpath(member.name, "store.rdf"),
                                    )
                                    if member.isdir():
                                        os.makedirs(member_path, exist_ok=True)
                                    else:
                                        member_file = tar.extractfile(member)
                                        if member_file:
                                            os.makedirs(
                                                os.path.dirname(member_path), exist_ok=True
                                            )
                                            with open(member_path, "wb") as f:
                                                f.write(member_file.read())
                    except KeyError:
                        raise BackupError("RDF store not found in backup")
            except tarfile.TarError as exc:
                raise BackupError(
                    "Corrupted backup archive", context={"suggestion": "Recreate the backup"}
                ) from exc

        # Restore from uncompressed backup
        else:
            if not os.path.exists(backup_path):
                raise BackupError(f"Backup directory not found: {backup_path}")

            # Copy DuckDB file
            db_source_path = os.path.join(backup_path, "db.duckdb")
            if os.path.exists(db_source_path):
                shutil.copy2(db_source_path, db_target_path)
            else:
                raise BackupError("DuckDB file not found in backup")

            # Copy RDF store
            rdf_source_path = os.path.join(backup_path, "store.rdf")
            if os.path.exists(rdf_source_path):
                if os.path.isdir(rdf_source_path):
                    # If it's a directory, copy the whole directory
                    shutil.copytree(
                        rdf_source_path, rdf_target_path, dirs_exist_ok=True
                    )
                else:
                    # If it's a file, copy it directly
                    shutil.copy2(rdf_source_path, rdf_target_path)
            else:
                raise BackupError("RDF store not found in backup")

        log.info(f"Restored backup from {backup_path} to {target_dir}")

        return {"db_path": db_target_path, "rdf_path": rdf_target_path}

    except BackupError:
        raise
    except tarfile.TarError as exc:
        log.error(f"Restore failed: {exc}")
        raise BackupError(
            "Corrupted backup archive", context={"suggestion": "Recreate the backup"}
        ) from exc
    except Exception as e:
        log.error(f"Restore failed: {e}")
        raise BackupError(f"Failed to restore backup: {e}") from e


def _list_backups(backup_dir: str) -> List[BackupInfo]:
    """List all backups in the specified directory.

    Args:
        backup_dir: Directory containing backups

    Returns:
        List of BackupInfo objects, sorted by timestamp (newest first)

    Raises:
        BackupError: If the backup directory doesn't exist or can't be read
    """
    try:
        if not os.path.exists(backup_dir):
            return []

        backups = []

        # Look for compressed backups
        for filename in os.listdir(backup_dir):
            if filename.startswith("backup_") and (
                filename.endswith(".tar.gz") or filename.endswith(".tgz")
            ):
                path = os.path.join(backup_dir, filename)

                # Extract timestamp from filename
                timestamp_str = (
                    filename.replace("backup_", "")
                    .replace(".tar.gz", "")
                    .replace(".tgz", "")
                )
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                except ValueError:
                    # Skip files with invalid timestamp format
                    continue

                size = os.path.getsize(path)

                backups.append(
                    BackupInfo(
                        path=path, timestamp=timestamp, compressed=True, size=size
                    )
                )

        # Look for uncompressed backups
        for dirname in os.listdir(backup_dir):
            if dirname.startswith("backup_") and os.path.isdir(
                os.path.join(backup_dir, dirname)
            ):
                path = os.path.join(backup_dir, dirname)

                # Extract timestamp from dirname
                timestamp_str = dirname.replace("backup_", "")
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                except ValueError:
                    # Skip directories with invalid timestamp format
                    continue

                # Calculate total size
                size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, _, filenames in os.walk(path)
                    for filename in filenames
                )

                backups.append(
                    BackupInfo(
                        path=path, timestamp=timestamp, compressed=False, size=size
                    )
                )

        # Sort by timestamp (newest first)
        backups.sort(key=lambda b: b.timestamp, reverse=True)

        return backups

    except Exception as e:
        log.error(f"Failed to list backups: {e}")
        raise BackupError(f"Failed to list backups: {e}")


def _apply_rotation_policy(backup_dir: str, config: BackupConfig) -> None:
    """Apply rotation policy to backups.

    This function enforces the backup retention policy by:
    1. Keeping only the most recent `max_backups` backups
    2. Removing backups older than `retention_days` days

    Args:
        backup_dir: Directory containing backups
        config: Backup configuration with rotation policy settings
    """
    try:
        backups = _list_backups(backup_dir)

        # Skip if no backups or only one backup
        if len(backups) <= 1:
            return

        # Calculate cutoff date for retention_days
        cutoff_date = datetime.now() - timedelta(days=config.retention_days)

        # Mark backups for deletion
        to_delete = []

        # Apply max_backups policy (keep the newest ones)
        if config.max_backups > 0 and len(backups) > config.max_backups:
            to_delete.extend(backups[config.max_backups:])

        # Apply retention_days policy
        if config.retention_days > 0:
            for backup in backups:
                if backup.timestamp < cutoff_date and backup not in to_delete:
                    to_delete.append(backup)

        # Delete marked backups
        for backup in to_delete:
            if os.path.exists(backup.path):
                if backup.compressed:
                    os.remove(backup.path)
                else:
                    shutil.rmtree(backup.path)
                log.info(f"Deleted old backup: {backup.path}")

    except Exception as e:
        log.error(f"Failed to apply rotation policy: {e}")
        # Don't raise an exception, just log the error


class BackupScheduler:
    """Scheduler for periodic backups."""

    def __init__(self):
        """Initialize the backup scheduler."""
        self._timer = None
        self._running = False
        self._lock = threading.Lock()

    def schedule(
        self,
        backup_dir: str,
        db_path: str,
        rdf_path: str,
        interval_hours: int = 24,
        compress: bool = True,
        max_backups: int = 5,
        retention_days: int = 30,
    ) -> None:
        """Schedule periodic backups.

        Args:
            backup_dir: Directory where backups will be stored
            db_path: Path to the DuckDB database file
            rdf_path: Path to the RDF store file or directory
            interval_hours: Interval between backups in hours
            compress: Whether to compress the backup
            max_backups: Maximum number of backups to keep
            retention_days: Maximum age of backups in days
        """
        with self._lock:
            if self._running:
                self.stop()

            self._running = True

            # Create backup config
            config = BackupConfig(
                backup_dir=backup_dir,
                compress=compress,
                max_backups=max_backups,
                retention_days=retention_days,
            )

            # Define the backup function
            def do_backup():
                try:
                    _create_backup(
                        backup_dir=backup_dir,
                        db_path=db_path,
                        rdf_path=rdf_path,
                        compress=compress,
                        config=config,
                    )
                except Exception as e:
                    log.error(f"Scheduled backup failed: {e}")
                finally:
                    # Schedule next backup if still running
                    with self._lock:
                        if self._running:
                            self._timer = threading.Timer(
                                interval_hours * 3600,  # Convert hours to seconds
                                do_backup,
                            )
                            self._timer.daemon = True
                            self._timer.start()

            # Start the first backup
            self._timer = threading.Timer(0, do_backup)  # Start immediately
            self._timer.daemon = True
            self._timer.start()

            log.info(f"Scheduled backups every {interval_hours} hours to {backup_dir}")

    def stop(self) -> None:
        """Stop scheduled backups."""
        with self._lock:
            self._running = False
            if self._timer:
                self._timer.cancel()
                # Joining ensures the timer thread has finished executing and
                # prevents lingering non-daemon threads from stalling test
                # shutdown. A short timeout avoids hanging if the thread fails
                # to terminate promptly.
                if hasattr(self._timer, "join"):
                    self._timer.join(timeout=1)
                self._timer = None
            log.info("Stopped scheduled backups")


class BackupManager:
    """Manager for backup and restore operations."""

    _scheduler = None

    @classmethod
    def get_scheduler(cls) -> BackupScheduler:
        """Get the backup scheduler instance."""
        if cls._scheduler is None:
            cls._scheduler = BackupScheduler()
        return cls._scheduler

    @staticmethod
    def create_backup(
        backup_dir: Optional[str] = None,
        db_path: Optional[str] = None,
        rdf_path: Optional[str] = None,
        compress: bool = True,
        config: Optional[BackupConfig] = None,
    ) -> BackupInfo:
        """Create a backup of the storage system.

        If paths are not provided, they will be determined from the configuration.

        Args:
            backup_dir: Directory where backups will be stored
            db_path: Path to the DuckDB database file
            rdf_path: Path to the RDF store file or directory
            compress: Whether to compress the backup
            config: Additional configuration for backup operations

        Returns:
            Information about the created backup

        Raises:
            BackupError: If the backup operation fails
        """
        # Get paths from configuration if not provided
        cfg = ConfigLoader().config.storage

        if backup_dir is None:
            backup_dir = cfg.backup_dir if hasattr(cfg, "backup_dir") else "backups"

        if db_path is None:
            db_path = (
                cfg.duckdb.path
                if hasattr(cfg, "duckdb") and hasattr(cfg.duckdb, "path")
                else "kg.duckdb"
            )

        if rdf_path is None:
            rdf_path = cfg.rdf_path if hasattr(cfg, "rdf_path") else "kg.rdf"

        return _create_backup(
            backup_dir=backup_dir,
            db_path=db_path,
            rdf_path=rdf_path,
            compress=compress,
            config=config,
        )

    @staticmethod
    def restore_backup(
        backup_path: str,
        target_dir: Optional[str] = None,
        db_filename: str = "db.duckdb",
        rdf_filename: str = "store.rdf",
    ) -> Dict[str, str]:
        """Restore a backup to the specified directory.

        Args:
            backup_path: Path to the backup to restore
            target_dir: Directory where the backup will be restored
            db_filename: Filename for the restored DuckDB database
            rdf_filename: Filename for the restored RDF store

        Returns:
            Dictionary with paths to the restored files

        Raises:
            BackupError: If the restore operation fails
        """
        if target_dir is None:
            target_dir = "restore_" + datetime.now().strftime("%Y%m%d_%H%M%S")

        return _restore_backup(
            backup_path=backup_path,
            target_dir=target_dir,
            db_filename=db_filename,
            rdf_filename=rdf_filename,
        )

    @staticmethod
    def list_backups(backup_dir: Optional[str] = None) -> List[BackupInfo]:
        """List all backups in the specified directory.

        Args:
            backup_dir: Directory containing backups

        Returns:
            List of BackupInfo objects, sorted by timestamp (newest first)

        Raises:
            BackupError: If the backup directory doesn't exist or can't be read
        """
        if backup_dir is None:
            cfg = ConfigLoader().config.storage
            backup_dir = cfg.backup_dir if hasattr(cfg, "backup_dir") else "backups"

        return _list_backups(backup_dir)

    @staticmethod
    def schedule_backup(
        backup_dir: Optional[str] = None,
        db_path: Optional[str] = None,
        rdf_path: Optional[str] = None,
        interval_hours: int = 24,
        compress: bool = True,
        max_backups: int = 5,
        retention_days: int = 30,
    ) -> None:
        """Schedule periodic backups.

        Args:
            backup_dir: Directory where backups will be stored
            db_path: Path to the DuckDB database file
            rdf_path: Path to the RDF store file or directory
            interval_hours: Interval between backups in hours
            compress: Whether to compress the backup
            max_backups: Maximum number of backups to keep
            retention_days: Maximum age of backups in days
        """
        # Get paths from configuration if not provided
        cfg = ConfigLoader().config.storage

        if backup_dir is None:
            backup_dir = cfg.backup_dir if hasattr(cfg, "backup_dir") else "backups"

        if db_path is None:
            db_path = (
                cfg.duckdb.path
                if hasattr(cfg, "duckdb") and hasattr(cfg.duckdb, "path")
                else "kg.duckdb"
            )

        if rdf_path is None:
            rdf_path = cfg.rdf_path if hasattr(cfg, "rdf_path") else "kg.rdf"

        # Schedule the backup
        scheduler = BackupManager.get_scheduler()
        scheduler.schedule(
            backup_dir=backup_dir,
            db_path=db_path,
            rdf_path=rdf_path,
            interval_hours=interval_hours,
            compress=compress,
            max_backups=max_backups,
            retention_days=retention_days,
        )

    @staticmethod
    def stop_scheduled_backups() -> None:
        """Stop scheduled backups."""
        if BackupManager._scheduler:
            BackupManager._scheduler.stop()

    @staticmethod
    def restore_point_in_time(
        backup_dir: str, target_time: datetime, target_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """Restore to a specific point in time.

        This method finds the backup closest to the specified time
        and restores it to the target directory.

        Args:
            backup_dir: Directory containing backups
            target_time: Target time to restore to
            target_dir: Directory where the backup will be restored

        Returns:
            Dictionary with paths to the restored files

        Raises:
            BackupError: If no suitable backup is found or restore fails
        """
        # List all backups
        backups = _list_backups(backup_dir)

        if not backups:
            raise BackupError(f"No backups found in {backup_dir}")

        # Find the backup closest to the target time
        closest_backup = min(
            backups, key=lambda b: abs((b.timestamp - target_time).total_seconds())
        )

        log.info(
            f"Restoring to point in time {target_time} using backup from {closest_backup.timestamp}"
        )

        # Restore the backup
        if target_dir is None:
            target_dir = f"restore_pit_{target_time.strftime('%Y%m%d_%H%M%S')}"

        return restore_backup(backup_path=closest_backup.path, target_dir=target_dir)


# Convenience wrapper functions


def create_backup(
    backup_dir: Optional[str] = None,
    db_path: Optional[str] = None,
    rdf_path: Optional[str] = None,
    compress: bool = True,
    config: Optional[BackupConfig] = None,
) -> BackupInfo:
    """Public API to create a storage backup."""
    return BackupManager.create_backup(
        backup_dir=backup_dir,
        db_path=db_path,
        rdf_path=rdf_path,
        compress=compress,
        config=config,
    )


def restore_backup(
    backup_path: str,
    target_dir: Optional[str] = None,
    db_filename: str = "db.duckdb",
    rdf_filename: str = "store.rdf",
) -> Dict[str, str]:
    """Public API to restore a backup."""
    return BackupManager.restore_backup(
        backup_path=backup_path,
        target_dir=target_dir,
        db_filename=db_filename,
        rdf_filename=rdf_filename,
    )


def list_backups(backup_dir: Optional[str] = None) -> List[BackupInfo]:
    """Public API to list available backups."""
    return BackupManager.list_backups(backup_dir)


def schedule_backup(
    backup_dir: Optional[str] = None,
    db_path: Optional[str] = None,
    rdf_path: Optional[str] = None,
    interval_hours: int = 24,
    compress: bool = True,
    max_backups: int = 5,
    retention_days: int = 30,
) -> None:
    """Public API to schedule recurring backups."""
    BackupManager.schedule_backup(
        backup_dir=backup_dir,
        db_path=db_path,
        rdf_path=rdf_path,
        interval_hours=interval_hours,
        compress=compress,
        max_backups=max_backups,
        retention_days=retention_days,
    )


def stop_scheduled_backups() -> None:
    """Public API to stop any scheduled backups."""
    BackupManager.stop_scheduled_backups()


def restore_point_in_time(
    backup_dir: str,
    target_time: datetime,
    target_dir: Optional[str] = None,
) -> Dict[str, str]:
    """Public API to restore to a specific point in time."""
    return BackupManager.restore_point_in_time(
        backup_dir=backup_dir,
        target_time=target_time,
        target_dir=target_dir,
    )
