import importlib.util
import sys
from pathlib import Path
from importlib import metadata

spec = importlib.util.spec_from_file_location(
    "check_env",
    Path(__file__).resolve().parents[2] / "scripts" / "check_env.py",
)
check_env = importlib.util.module_from_spec(spec)
sys.modules["check_env"] = check_env
spec.loader.exec_module(check_env)


def test_missing_package_metadata_warns(monkeypatch, capsys):
    monkeypatch.setattr(check_env, "REQUIREMENTS", {"fakepkg": "1.0"})

    def fake_version(name):
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(check_env.metadata, "version", lambda name: fake_version(name))
    result = check_env.check_package("fakepkg")
    captured = capsys.readouterr()
    assert result is None
    assert "WARNING: package metadata not found for fakepkg" in captured.err


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
    check_env.main()
    captured = capsys.readouterr()
    assert "WARNING: package metadata not found for fakepkg" in captured.err
    assert "ERROR" not in captured.err
