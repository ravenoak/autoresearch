"""Integration tests for deployment configuration validation."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


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
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )


def test_deploy_validation_offline(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "SERPER_API_KEY": "key",
            "AUTORESEARCH_ACTIVE_PROFILE": "offline",
            "AUTORESEARCH_HEALTHCHECK_URL": "",
        }
    )
    result = _run_deploy(tmp_path, env)
    assert result.returncode == 0
    assert "Configuration valid" in result.stdout


def test_deploy_validation_online_missing_key(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "SERPER_API_KEY": "key",
            "AUTORESEARCH_ACTIVE_PROFILE": "online",
            "AUTORESEARCH_HEALTHCHECK_URL": "",
        }
    )
    result = _run_deploy(tmp_path, env)
    assert result.returncode != 0
    assert "OPENAI_API_KEY" in result.stdout


def test_deploy_validation_online(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "SERPER_API_KEY": "key",
            "OPENAI_API_KEY": "openai",
            "AUTORESEARCH_ACTIVE_PROFILE": "online",
            "AUTORESEARCH_HEALTHCHECK_URL": "",
        }
    )
    result = _run_deploy(tmp_path, env)
    assert result.returncode == 0
    assert "Configuration valid" in result.stdout


def _run_validate(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[2] / "scripts" / "validate_deploy.py"
    return subprocess.run(
        [sys.executable, str(script)],
        env=env,
        capture_output=True,
        text=True,
    )


def test_validate_deploy_success(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: 1\nservices:\n- api\n")
    (tmp_path / ".env").write_text("KEY=value\n")
    env = os.environ.copy()
    env["DEPLOY_ENV"] = "production"
    env["CONFIG_DIR"] = str(tmp_path)
    result = _run_validate(env)
    assert result.returncode == 0
    assert "validated" in result.stdout.lower()


def test_validate_deploy_missing_env(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: 1\nservices:\n- api\n")
    (tmp_path / ".env").write_text("KEY=value\n")
    env = os.environ.copy()
    env.pop("DEPLOY_ENV", None)
    env["CONFIG_DIR"] = str(tmp_path)
    result = _run_validate(env)
    assert result.returncode != 0
    assert "DEPLOY_ENV" in result.stderr


def test_validate_deploy_missing_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("KEY=value\n")
    env = os.environ.copy()
    env["DEPLOY_ENV"] = "production"
    env["CONFIG_DIR"] = str(tmp_path)
    result = _run_validate(env)
    assert result.returncode != 0
    assert "deploy.yml" in result.stderr


def test_validate_deploy_yaml_schema_error(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: []\n")
    (tmp_path / ".env").write_text("KEY=value\n")
    env = os.environ.copy()
    env["DEPLOY_ENV"] = "production"
    env["CONFIG_DIR"] = str(tmp_path)
    result = _run_validate(env)
    assert result.returncode != 0
    assert "deploy.yml" in result.stderr


def test_validate_deploy_env_schema_error(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: 1\nservices:\n- api\n")
    (tmp_path / ".env").write_text("KEY=\n")
    env = os.environ.copy()
    env["DEPLOY_ENV"] = "production"
    env["CONFIG_DIR"] = str(tmp_path)
    result = _run_validate(env)
    assert result.returncode != 0
    assert ".env" in result.stderr
