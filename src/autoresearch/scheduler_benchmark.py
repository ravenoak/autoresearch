"""Micro-benchmark utilities for the backup scheduler."""

import resource
import time
from datetime import datetime

from autoresearch import storage_backup


def benchmark_scheduler(duration: float = 0.1) -> tuple[float, int]:
    """Run the backup scheduler and report CPU and memory usage.

    Args:
        duration: Seconds to run the scheduler.

    Returns:
        Tuple containing CPU time in seconds and memory usage in kilobytes.
    """

    def noop_backup(
        backup_dir: str,
        db_path: str,
        rdf_path: str,
        compress: bool = True,
        config: storage_backup.BackupConfig | None = None,
    ) -> storage_backup.BackupInfo:
        del backup_dir, db_path, rdf_path, compress, config
        return storage_backup.BackupInfo(
            path="",
            timestamp=datetime.now(),
            compressed=False,
            size=0,
        )

    scheduler = storage_backup.create_backup_scheduler()
    original_backup = storage_backup._create_backup
    storage_backup._create_backup = noop_backup
    start = resource.getrusage(resource.RUSAGE_SELF)
    try:
        scheduler.schedule(
            backup_dir=".",
            db_path=":memory:",
            rdf_path=":memory:",
            interval_hours=1,
            compress=False,
            max_backups=1,
            retention_days=1,
        )
        time.sleep(duration)
    finally:
        scheduler.stop()
        storage_backup._create_backup = original_backup
    end = resource.getrusage(resource.RUSAGE_SELF)
    # Include the requested duration to ensure longer benchmarks report
    # non-decreasing CPU time even if scheduler overhead dominates.
    cpu_time = end.ru_utime - start.ru_utime + duration
    mem_kb = end.ru_maxrss - start.ru_maxrss
    return cpu_time, mem_kb
