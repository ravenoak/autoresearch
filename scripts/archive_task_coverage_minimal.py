"""Archive a minimal coverage run for baseline tracking.

Usage:
    uv run python scripts/archive_task_coverage_minimal.py
"""

from __future__ import annotations

import datetime as _datetime
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_EXPECTED_LOG_TAIL = "coverage report --fail-under=90"


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


def _validate_log_tail(log_path: Path) -> None:
    """Ensure the final non-empty log line confirms the coverage threshold."""

    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    last_non_empty: str | None = None
    with log_path.open("r", encoding="utf-8") as log_file:
        for line in log_file:
            stripped = line.strip()
            if stripped:
                last_non_empty = stripped

    if last_non_empty is None:
        raise ValueError("Coverage log is empty; expected coverage command output.")

    if last_non_empty != _EXPECTED_LOG_TAIL:
        raise ValueError(
            "Unexpected final log line."
            f" Expected '{_EXPECTED_LOG_TAIL}' but saw '{last_non_empty}'."
        )


def _validate_coverage_xml(coverage_file: Path) -> None:
    """Validate that ``coverage.xml`` reports at least 90% line coverage."""

    if not coverage_file.exists():
        raise FileNotFoundError(f"coverage.xml not found: {coverage_file}")

    try:
        root = ET.parse(coverage_file).getroot()
    except ET.ParseError as exc:  # pragma: no cover - defensive guard
        raise ValueError("Unable to parse coverage.xml") from exc

    tag = root.tag.split("}", 1)[-1] if "}" in root.tag else root.tag
    if tag != "coverage":
        raise ValueError("coverage.xml does not contain a <coverage> root element.")

    line_rate_attr = root.attrib.get("line-rate")
    if line_rate_attr is None:
        raise ValueError("coverage.xml missing required line-rate attribute.")

    try:
        line_rate = float(line_rate_attr)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError("coverage.xml line-rate is not a valid number.") from exc

    if line_rate < 0.9:
        raise ValueError(
            f"Coverage line-rate {line_rate:.3f} is below the 0.900 requirement."
        )


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

    for existing_snapshot in archive_dir.iterdir():
        if existing_snapshot.is_dir() and existing_snapshot.name != timestamp:
            stale_htmlcov = existing_snapshot / "htmlcov"
            if stale_htmlcov.exists():
                shutil.rmtree(stale_htmlcov)
                print(f"Removed stale coverage dossier: {stale_htmlcov}")

    baseline_xml = baseline_dir / "coverage.xml"
    snapshot_xml = archive_dir / f"{timestamp}.xml"

    shutil.copy2(coverage_file, baseline_xml)
    shutil.copy2(coverage_file, snapshot_xml)

    _validate_coverage_xml(baseline_xml)
    _validate_coverage_xml(snapshot_xml)

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
    _validate_log_tail(log_path)
    _validate_coverage_xml(Path("coverage.xml"))
    _copy_coverage_outputs(timestamp)

    baseline_xml = Path("baseline") / "coverage.xml"
    snapshot_xml = Path("baseline") / "archive" / f"{timestamp}.xml"
    print(
        "Archived minimal coverage snapshot "
        f"{timestamp}: log={log_path}, baseline_xml={baseline_xml}, "
        f"archive_xml={snapshot_xml}"
    )


if __name__ == "__main__":
    main()

