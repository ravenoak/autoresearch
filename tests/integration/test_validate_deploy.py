"""Tests for ``scripts/validate_deploy.py``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

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


def test_validate_deploy_missing_env_file(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: 1\n")
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert ".env" in result.stderr


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


def test_validate_deploy_valid_extra(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path), "EXTRAS": "analysis"})
    result = _run(env, tmp_path)
    assert result.returncode == 0
    assert "validated" in result.stdout.lower()


def test_validate_deploy_unknown_extra(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path), "EXTRAS": "unknown"})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "Unknown extras" in result.stderr


def test_validate_deploy_unsupported_engine(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": "production",
            "CONFIG_DIR": str(tmp_path),
            "CONTAINER_ENGINE": "no-such-engine",
        }
    )
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "Unsupported container engine" in result.stderr


def test_validate_deploy_engine_not_found(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": "production",
            "CONFIG_DIR": str(tmp_path),
            "CONTAINER_ENGINE": "podman",
        }
    )
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "not found" in result.stderr


def test_validate_deploy_invalid_yaml(tmp_path: Path) -> None:
    (tmp_path / "deploy.yml").write_text("version: [\n")
    (tmp_path / ".env").write_text("KEY=value\n")
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "Invalid YAML" in result.stderr


def test_validate_deploy_duplicate_env_key(tmp_path: Path) -> None:
    _write_config(tmp_path, env_content="KEY=one\nKEY=two\n")
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "Duplicate key" in result.stderr


@pytest.mark.parametrize("env_name", ["linux", "macos", "windows", "production"])
def test_validate_deploy_env_samples(tmp_path: Path, env_name: str) -> None:
    config_dir = tmp_path / env_name
    config_dir.mkdir()
    _write_config(config_dir)
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": env_name, "CONFIG_DIR": str(config_dir)})
    result = _run(env, config_dir)
    assert result.returncode == 0
    assert "validated" in result.stdout.lower()


def test_validate_deploy_invalid_env(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "unknown", "CONFIG_DIR": str(tmp_path)})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "DEPLOY_ENV must be one of" in result.stderr


def test_validate_deploy_missing_config_dir(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(missing)})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "CONFIG_DIR not found" in result.stderr


def test_validate_deploy_relative_config_dir(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": "relative"})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "absolute" in result.stderr


@pytest.mark.slow
def test_validate_deploy_scans_all_configs(tmp_path: Path) -> None:
    deploy_dir = tmp_path / "deploy"
    good = deploy_dir / "good"
    good.mkdir(parents=True)
    _write_config(good)
    extra = deploy_dir / "extra"
    extra.mkdir()
    _write_config(extra)
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": "good",
            "CONFIG_DIR": str(good),
            "DEPLOY_DIR": str(deploy_dir),
        }
    )
    result = _run(env, tmp_path)
    assert result.returncode == 0
    assert "validated" in result.stdout.lower()


@pytest.mark.slow
def test_validate_deploy_scans_and_fails(tmp_path: Path) -> None:
    deploy_dir = tmp_path / "deploy"
    good = deploy_dir / "good"
    good.mkdir(parents=True)
    _write_config(good)
    bad = deploy_dir / "bad"
    bad.mkdir()
    _write_config(bad, env_content="OTHER=1\n")
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": "good",
            "CONFIG_DIR": str(good),
            "DEPLOY_DIR": str(deploy_dir),
        }
    )
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "bad" in result.stderr
