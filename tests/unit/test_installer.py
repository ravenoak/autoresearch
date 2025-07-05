"""Tests for the :mod:`scripts.installer` module."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "installer", Path(__file__).resolve().parents[2] / "scripts" / "installer.py"
)
installer = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(installer)


def _run_installer(monkeypatch, argv, optional, installed):
    calls = []

    monkeypatch.setattr(installer, "get_optional_dependencies", lambda: optional)
    monkeypatch.setattr(installer, "get_installed_packages", lambda: installed)

    def fake_check_call(cmd):
        calls.append(cmd)

    monkeypatch.setattr(installer.subprocess, "check_call", fake_check_call)
    monkeypatch.setattr(installer.sys, "argv", ["installer.py", *argv])
    installer.main()
    return calls


def test_minimal_install(monkeypatch):
    calls = _run_installer(
        monkeypatch,
        ["--minimal"],
        {"minimal": ["a"], "extra": ["b"]},
        set(),
    )

    assert ["poetry", "env", "use", installer.sys.executable] in calls
    assert [
        "poetry",
        "install",
        "--with",
        "dev",
        "--extras",
        "minimal",
    ] in calls
    assert all("update" not in c for c in calls)


def test_full_auto_resolution(monkeypatch):
    calls = _run_installer(
        monkeypatch,
        [],
        {"minimal": ["a"], "extra": ["b"]},
        {"a"},
    )

    assert any("--extras" in c for c in calls)
    assert ["poetry", "update"] not in calls


def test_upgrade(monkeypatch):
    calls = _run_installer(
        monkeypatch,
        ["--upgrade"],
        {"minimal": ["a"], "extra": ["b"]},
        {"a", "b"},
    )

    assert calls[-1] == ["poetry", "update"]
