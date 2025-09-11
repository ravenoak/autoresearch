import importlib.util
import sys
from importlib import metadata
from pathlib import Path
import builtins
import pytest

spec = importlib.util.spec_from_file_location(
    "check_env",
    Path(__file__).resolve().parents[2] / "scripts" / "check_env.py",
)
check_env = importlib.util.module_from_spec(spec)
sys.modules["check_env"] = check_env
spec.loader.exec_module(check_env)


def test_missing_package_metadata_warns(monkeypatch):
    monkeypatch.setattr(check_env, "REQUIREMENTS", {"fakepkg": "1.0"})

    def fake_version(name):
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(check_env.metadata, "version", fake_version)
    with pytest.warns(UserWarning, match="package metadata not found for fakepkg"):
        result = check_env.check_package("fakepkg")
    assert result is None


def test_missing_pytest_bdd_warns(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pytest_bdd":
            raise ModuleNotFoundError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.warns(UserWarning, match="pytest-bdd import failed; run 'task install'."):
        result = check_env.check_pytest_bdd()
    assert result is None


def test_missing_go_task_warns(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(check_env.subprocess, "run", fake_run)
    with pytest.warns(
        UserWarning,
        match="Go Task .* not found; install it from https://taskfile.dev/ or run scripts/bootstrap.sh",
    ):
        result = check_env.check_task()
    assert result is None


def test_main_ignores_missing_metadata(monkeypatch, capsys):
    monkeypatch.setattr(check_env, "EXTRA_REQUIREMENTS", {"fakepkg": "1.0"})
    monkeypatch.setattr(check_env, "REQUIREMENTS", {"fakepkg": "1.0"})
    dummy = check_env.CheckResult("ok", "1", "1")
    monkeypatch.setattr(check_env, "check_python", lambda: dummy)
    monkeypatch.setattr(check_env, "check_task", lambda: dummy)
    monkeypatch.setattr(check_env, "check_uv", lambda: dummy)
    monkeypatch.setattr(sys, "argv", ["check_env.py"])

    def fake_version(name):
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(check_env.metadata, "version", lambda name: fake_version(name))
    with pytest.warns(UserWarning, match="package metadata not found for fakepkg"):
        check_env.main()
    captured = capsys.readouterr()
    assert "ERROR" not in captured.err
