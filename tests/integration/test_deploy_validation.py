# mypy: ignore-errors
"""Integration tests for deployment configuration validation."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BASE_ENV = {
    "PATH": os.getenv("PATH", ""),
    "PYTHONPATH": os.getenv("PYTHONPATH", ""),
    "HOME": os.getenv("HOME", ""),
}


def _write_config(tmp_path: Path) -> None:
    cfg_text = """
[core]
llm_backend = "openai"

[search]
backends = ["serper"]

[profiles.offline]
llm_backend = "lmstudio"

[profiles.online]
llm_backend = "openai"
"""
    (tmp_path / "autoresearch.toml").write_text(cfg_text)


def _run_deploy(tmp_path: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[2] / "scripts" / "deploy.py"
    run_env = {**BASE_ENV, **env}
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        env=run_env,
        capture_output=True,
        text=True,
    )


def test_deploy_validation_offline(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = {
        "SERPER_API_KEY": "key",
        "AUTORESEARCH_ACTIVE_PROFILE": "offline",
        "AUTORESEARCH_HEALTHCHECK_URL": "",
    }
    result = _run_deploy(tmp_path, env)
    assert result.returncode == 0
    assert "Configuration valid" in result.stdout


def test_deploy_validation_online_missing_key(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = {
        "SERPER_API_KEY": "key",
        "AUTORESEARCH_ACTIVE_PROFILE": "online",
        "AUTORESEARCH_HEALTHCHECK_URL": "",
    }
    result = _run_deploy(tmp_path, env)
    assert result.returncode != 0
    assert "OPENAI_API_KEY" in result.stdout


def test_deploy_validation_online(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = {
        "SERPER_API_KEY": "key",
        "OPENAI_API_KEY": "openai",
        "AUTORESEARCH_ACTIVE_PROFILE": "online",
        "AUTORESEARCH_HEALTHCHECK_URL": "",
    }
    result = _run_deploy(tmp_path, env)
    assert result.returncode == 0
    assert "Configuration valid" in result.stdout


def _run_validate(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[2] / "scripts" / "validate_deploy.py"
    run_env = {**BASE_ENV, **env}
    return subprocess.run(
        [sys.executable, str(script)],
        env=run_env,
        capture_output=True,
        text=True,
    )


def test_validate_deploy_success(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: 1\nservices: [app]\n")
    (tmp_path / ".env").write_text("KEY=value\n")
    env = {"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)}
    result = _run_validate(env)
    assert result.returncode == 0
    assert "validated" in result.stdout.lower()


def test_validate_deploy_missing_env(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: 1\nservices: [app]\n")
    (tmp_path / ".env").write_text("KEY=value\n")
    env = {"CONFIG_DIR": str(tmp_path)}
    result = _run_validate(env)
    assert result.returncode != 0
    assert "DEPLOY_ENV" in result.stderr


def test_validate_deploy_missing_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("KEY=value\n")
    env = {"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)}
    result = _run_validate(env)
    assert result.returncode != 0
    assert "deploy.yml" in result.stderr


def test_validate_deploy_yaml_schema_error(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: []\nservices: [app]\n")
    (tmp_path / ".env").write_text("KEY=value\n")
    env = {"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)}
    result = _run_validate(env)
    assert result.returncode != 0
    assert "Schema errors in deploy.yml" in result.stderr
    assert "version" in result.stderr


def test_validate_deploy_env_schema_error(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: 1\nservices: [app]\n")
    (tmp_path / ".env").write_text("KEY=\n")
    env = {"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)}
    result = _run_validate(env)
    assert result.returncode != 0
    assert "Schema errors in .env" in result.stderr
    assert "KEY" in result.stderr
