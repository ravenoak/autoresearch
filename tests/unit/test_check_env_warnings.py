import importlib.util
import sys
from importlib import metadata
from pathlib import Path
import builtins
import pytest
from typing import Any

spec = importlib.util.spec_from_file_location(
    "check_env",
    Path(__file__).resolve().parents[2] / "scripts" / "check_env.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load check_env module")
check_env = importlib.util.module_from_spec(spec)
sys.modules["check_env"] = check_env
spec.loader.exec_module(check_env)


@pytest.fixture()
def missing_fakepkg(monkeypatch):
    monkeypatch.setattr(check_env, "REQUIREMENTS", {"fakepkg": "1.0"})

    def fake_version(name: str) -> str:  # pragma: no cover - stub
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(check_env.metadata, "version", fake_version)


def test_missing_package_metadata_raises(missing_fakepkg: Any) -> None:
    with pytest.raises(check_env.VersionError, match="fakepkg not installed; run 'task install'"):
        check_env.check_package("fakepkg")


def test_missing_pytest_bdd_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pytest_bdd":
            raise ModuleNotFoundError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(check_env.VersionError, match="pytest-bdd is required; run 'task install'"):
        check_env.check_pytest_bdd()


def test_missing_go_task_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(check_env.subprocess, "run", fake_run)
    with pytest.raises(
        check_env.VersionError,
        match="Go Task .* not found; install it with scripts/setup.sh or your package manager",
    ):
        check_env.check_task()


def test_missing_uv_raises_version_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(check_env.subprocess, "run", fake_run)
    with pytest.raises(check_env.VersionError, match="uv is not installed"):
        check_env.check_uv()


def test_task_command_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-zero task exit should raise a VersionError with guidance."""

    class Proc:
        returncode = 1
        stdout = ""

    monkeypatch.setattr(check_env.subprocess, "run", lambda *a, **k: Proc())
    with pytest.raises(check_env.VersionError, match="Go Task .* is required"):
        check_env.check_task()


def test_main_reports_missing_metadata(missing_fakepkg: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(check_env, "EXTRA_REQUIREMENTS", {"fakepkg": "1.0"})
    dummy = check_env.CheckResult("ok", "1", "1")
    monkeypatch.setattr(check_env, "check_python", lambda: dummy)
    monkeypatch.setattr(check_env, "check_task", lambda: dummy)
    monkeypatch.setattr(check_env, "check_uv", lambda: dummy)
    monkeypatch.setattr(sys, "argv", ["check_env.py"])

    with pytest.raises(SystemExit):
        check_env.main()
    captured = capsys.readouterr()
    assert "fakepkg not installed" in captured.err
