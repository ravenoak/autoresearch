from __future__ import annotations

from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verify_coverage_log.py"


def test_verify_coverage_log_pass(tmp_path: Path) -> None:
    log = tmp_path / "log.txt"
    log.write_text("DONE\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), str(log)])
    assert result.returncode == 0


def test_verify_coverage_log_fail(tmp_path: Path) -> None:
    log = tmp_path / "log.txt"
    log.write_text("", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), str(log)])
    assert result.returncode != 0
