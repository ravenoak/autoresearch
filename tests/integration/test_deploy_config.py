"""Integration tests for deploy configuration content validation."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run_validate(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[2] / "scripts" / "validate_deploy.py"
    env = os.environ.copy()
    env["DEPLOY_ENV"] = "production"
    env["CONFIG_DIR"] = str(tmp_path)
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )


def _write_configs(tmp_path: Path, yaml_text: str, env_text: str) -> None:
    (tmp_path / "deploy.yml").write_text(yaml_text)
    (tmp_path / ".env").write_text(env_text)


def test_validate_success(tmp_path: Path) -> None:
    _write_configs(tmp_path, "version: 1\n", "KEY=value\n")
    result = _run_validate(tmp_path)
    assert result.returncode == 0
    assert "validated" in result.stdout.lower()


def test_missing_yaml_key(tmp_path: Path) -> None:
    _write_configs(tmp_path, "other: 1\n", "KEY=value\n")
    result = _run_validate(tmp_path)
    assert result.returncode != 0
    assert "version" in result.stderr


def test_missing_env_key(tmp_path: Path) -> None:
    _write_configs(tmp_path, "version: 1\n", "")
    result = _run_validate(tmp_path)
    assert result.returncode != 0
    assert "KEY" in result.stderr
