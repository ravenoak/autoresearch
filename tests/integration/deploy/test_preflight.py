# mypy: ignore-errors
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "validate_deploy.py"


def _write_config(tmp_path: Path, services: list[str] | None = None) -> None:
    services = services or ["api"]
    srv = ", ".join(services)
    (tmp_path / "deploy.yml").write_text(f"version: 1\nservices: [{srv}]\n")
    (tmp_path / ".env").write_text("KEY=value\n")


def _run(env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def test_preflight_success(tmp_path: Path) -> None:
    _write_config(tmp_path, ["api", "worker"])
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": "production",
            "CONFIG_DIR": str(tmp_path),
            "REQUIRED_SERVICES": "api worker",
        }
    )
    result = _run(env, tmp_path)
    assert result.returncode == 0
    assert "validated" in result.stdout.lower()


def test_preflight_missing_env(tmp_path: Path) -> None:
    _write_config(tmp_path)
    env = os.environ.copy()
    env.pop("DEPLOY_ENV", None)
    env["CONFIG_DIR"] = str(tmp_path)
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "DEPLOY_ENV" in result.stderr


def test_preflight_missing_config_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("KEY=value\n")
    env = os.environ.copy()
    env.update({"DEPLOY_ENV": "production", "CONFIG_DIR": str(tmp_path)})
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "deploy.yml" in result.stderr


def test_preflight_missing_service(tmp_path: Path) -> None:
    _write_config(tmp_path, ["api"])
    env = os.environ.copy()
    env.update(
        {
            "DEPLOY_ENV": "production",
            "CONFIG_DIR": str(tmp_path),
            "REQUIRED_SERVICES": "api worker",
        }
    )
    result = _run(env, tmp_path)
    assert result.returncode != 0
    assert "missing required services" in result.stderr.lower()
