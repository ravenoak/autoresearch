"""Tests for ``scripts/validate_deploy.py``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "validate_deploy.py"


def _run(env: dict[str, str], tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )


def _write_config(
    tmp_path: Path,
    yaml_content: str = "version: 1\n",
    env_content: str = "KEY=value\n",
) -> None:
    (tmp_path / "deploy.yml").write_text(yaml_content)
    (tmp_path / ".env").write_text(env_content)


def test_validate_deploy_success(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)})
    result = _run(env, tmp_path)
    assert result.returncode == 0
    assert "validated" in result.stdout.lower()


def test_validate_deploy_missing_env(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.pop("DEPLOY_ENV", None)
    env["CONFIG_DIR"] = str(tmp_path)
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "DEPLOY_ENV" in result.stderr


def test_validate_deploy_missing_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("KEY=value\n")
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "deploy.yml" in result.stderr


def test_validate_deploy_missing_yaml_key(tmp_path: Path) -> None:
    _write_config(tmp_path, yaml_content="{}\n")
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "version" in result.stderr


def test_validate_deploy_missing_env_key(tmp_path: Path) -> None:
    _write_config(tmp_path, env_content="OTHER=value\n")
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "KEY" in result.stderr
