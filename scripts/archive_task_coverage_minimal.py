"""Archive a minimal coverage run for baseline tracking.

Usage:
    uv run python scripts/archive_task_coverage_minimal.py
"""

from __future__ import annotations

import datetime as _datetime
import shutil
import subprocess
import sys
from pathlib import Path


def _run_coverage_minimal(log_path: Path) -> None:
    """Execute the minimal coverage task and tee its output to ``log_path``."""

    command = ["uv", "run", "task", "coverage:minimal"]
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        assert process.stdout is not None  # For type checkers.
        for line in process.stdout:
            sys.stdout.write(line)
            log_file.write(line)

        process.wait()

    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command)


def _copy_coverage_outputs(timestamp: str) -> None:
    """Copy coverage artifacts into baseline snapshots for the given timestamp."""

    project_root = Path(".")
    coverage_file = project_root / "coverage.xml"
    if not coverage_file.exists():
        raise FileNotFoundError(
            "coverage.xml not found. Ensure the coverage task completed successfully."
        )

    baseline_dir = project_root / "baseline"
    archive_dir = baseline_dir / "archive"
    snapshot_dir = archive_dir / timestamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(coverage_file, baseline_dir / "coverage.xml")
    shutil.copy2(coverage_file, archive_dir / f"{timestamp}.xml")

    htmlcov_src = project_root / "htmlcov"
    if not htmlcov_src.exists():
        raise FileNotFoundError(
            "htmlcov directory not found. Run coverage:minimal before archiving."
        )

    htmlcov_dest = snapshot_dir / "htmlcov"
    if htmlcov_dest.exists():
        shutil.rmtree(htmlcov_dest)
    shutil.copytree(htmlcov_src, htmlcov_dest)


def main() -> None:
    timestamp = _datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    log_path = Path("baseline/logs") / f"task-coverage-{timestamp}.log"

    _run_coverage_minimal(log_path)
    _copy_coverage_outputs(timestamp)


if __name__ == "__main__":
    main()

