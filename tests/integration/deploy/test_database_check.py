# mypy: ignore-errors
from __future__ import annotations

"""Database connectivity checks for ``scripts/validate_deploy.py``."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "validate_deploy.py"


def _write_config(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: 1\nservices: [api]\n")
    (tmp_path / ".env").write_text("KEY=value\n")


def _run(env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def test_database_available(tmp_path: Path) -> None:
    _write_config(tmp_path)
    db_path = tmp_path / "db.sqlite"
    sqlite3.connect(db_path).close()
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": "production",
            "CONFIG_DIR": str(tmp_path),
            "DATABASE_URL": f"sqlite:///{db_path}",
        }
    )
    result = _run(env, tmp_path)
    assert result.returncode == 0
    assert "validated" in result.stdout.lower()


def test_database_unavailable(tmp_path: Path) -> None:
    _write_config(tmp_path)
    bad_path = tmp_path / "missing" / "db.sqlite"
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": "production",
            "CONFIG_DIR": str(tmp_path),
            "DATABASE_URL": f"sqlite:///{bad_path}",
        }
    )
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "database unavailable" in result.stderr.lower()
