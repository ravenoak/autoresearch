# mypy: ignore-errors
from __future__ import annotations

import builtins
import importlib.util
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

import pytest

spec = importlib.util.spec_from_file_location(
    "check_env",
    Path(__file__).resolve().parents[2] / "scripts" / "check_env.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load check_env module")
check_env = importlib.util.module_from_spec(spec)
sys.modules["check_env"] = check_env
spec.loader.exec_module(check_env)


@pytest.fixture(name="_missing_fakepkg")
def missing_fakepkg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_env, "REQUIREMENTS", {"fakepkg": "1.0"})

    def fake_version(name: str) -> str:  # pragma: no cover - stub
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(check_env.metadata, "version", fake_version)


def test_missing_package_metadata_raises(_missing_fakepkg: None) -> None:
    with pytest.raises(check_env.VersionError, match="fakepkg not installed; run 'task install'"):
        check_env.check_package("fakepkg")


def test_missing_pytest_bdd_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "pytest_bdd":
            raise ModuleNotFoundError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(check_env.VersionError, match="pytest-bdd is required; run 'task install'"):
        check_env.check_pytest_bdd()


def test_missing_go_task_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(check_env.subprocess, "run", fake_run)
    with pytest.raises(
        check_env.VersionError,
        match="Go Task .* not found; install it with scripts/setup.sh or your package manager",
    ):
        check_env.check_task()


def test_missing_uv_raises_version_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(check_env.subprocess, "run", fake_run)
    with pytest.raises(check_env.VersionError, match="uv is not installed"):
        check_env.check_uv()


def test_task_command_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-zero task exit should raise a VersionError with guidance."""

    class Proc:
        returncode: int = 1
        stdout: str = ""

    def _run(*args: Any, **kwargs: Any) -> Proc:
        return Proc()

    monkeypatch.setattr(check_env.subprocess, "run", _run)
    with pytest.raises(check_env.VersionError, match="Go Task .* is required"):
        check_env.check_task()


def test_main_reports_missing_metadata(
    _missing_fakepkg: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(check_env, "EXTRA_REQUIREMENTS", {"fakepkg": "1.0"})
    dummy = check_env.CheckResult("ok", "1", "1")

    def _check_python() -> check_env.CheckResult:
        return dummy

    def _check_task() -> check_env.CheckResult:
        return dummy

    def _check_uv() -> check_env.CheckResult:
        return dummy

    monkeypatch.setattr(check_env, "check_python", _check_python)
    monkeypatch.setattr(check_env, "check_task", _check_task)
    monkeypatch.setattr(check_env, "check_uv", _check_uv)
    monkeypatch.setattr(sys, "argv", ["check_env.py"])

    with pytest.raises(SystemExit):
        check_env.main()
    captured = capsys.readouterr()
    assert "fakepkg not installed" in captured.err


def test_env_metadata_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_env, "REQUIREMENTS", {"fakepkg": "1.0"})

    def fake_version(name: str) -> str:  # pragma: no cover - stub
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(check_env.metadata, "version", fake_version)
    monkeypatch.setenv("AUTORESEARCH_FAKEPKG_VERSION", "2.0")
    result = check_env.check_package("fakepkg")
    assert result is not None
    assert result.current == "2.0"
