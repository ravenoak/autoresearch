"""Integration tests for deployment helpers across platforms."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_config(path: Path) -> Path:
    """Create deployment configuration and return the config directory."""
    config_dir = path / "config"
    config_dir.mkdir()
    (config_dir / "deploy.yml").write_text("version: 1\nservices: [api]\n")
    (config_dir / ".env").write_text("KEY=value\n")
    cfg_file = path / "autoresearch.toml"
    cfg_file.write_text("[core]\nbackend='lmstudio'\nloops=1\n[search]\nbackends=[]\n")
    return config_dir


@pytest.mark.parametrize(
    "env_name, script",
    [
        ("linux", REPO_ROOT / "scripts" / "deploy" / "linux.sh"),
        ("macos", REPO_ROOT / "scripts" / "deploy" / "macos.sh"),
    ],
)
def test_bash_deploy_scripts(env_name: str, script: Path, tmp_path: Path) -> None:
    config_dir = _write_config(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": env_name,
            "CONFIG_DIR": str(config_dir),
            "AUTORESEARCH_CONFIG_FILE": str(tmp_path / "autoresearch.toml"),
            "AUTORESEARCH_HEALTHCHECK_URL": "",
            "SERPER_API_KEY": "dummy",
            "BRAVE_SEARCH_API_KEY": "dummy",
            "OPENAI_API_KEY": "dummy",
            "OPENROUTER_API_KEY": "dummy",
        }
    )
    result = subprocess.run(
        ["bash", str(script)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Deployment configuration validated." in result.stdout
    assert "Configuration valid" in result.stdout


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh not installed")
def test_windows_deploy_script(tmp_path: Path) -> None:
    script = REPO_ROOT / "scripts" / "deploy" / "windows.ps1"
    config_dir = _write_config(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": "windows",
            "CONFIG_DIR": str(config_dir),
            "AUTORESEARCH_CONFIG_FILE": str(tmp_path / "autoresearch.toml"),
            "AUTORESEARCH_HEALTHCHECK_URL": "",
            "SERPER_API_KEY": "dummy",
            "BRAVE_SEARCH_API_KEY": "dummy",
            "OPENAI_API_KEY": "dummy",
            "OPENROUTER_API_KEY": "dummy",
        }
    )
    result = subprocess.run(
        ["pwsh", str(script)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Deployment configuration validated." in result.stdout
    assert "Configuration valid" in result.stdout
