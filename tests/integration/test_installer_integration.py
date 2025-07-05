from pathlib import Path
import sys
import tomllib

import importlib.util

INSTALLER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "installer.py"
spec = importlib.util.spec_from_file_location("installer", INSTALLER_PATH)
installer = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(installer)  # type: ignore


def _run(monkeypatch, args):
    cmds = []
    monkeypatch.setattr(installer, "run", lambda cmd: cmds.append(cmd))
    monkeypatch.setattr(sys, "argv", ["installer.py"] + args)
    monkeypatch.chdir(Path(__file__).resolve().parents[2])
    installer.main()
    return cmds


def test_installer_extras(monkeypatch):
    cmds = _run(monkeypatch, ["--minimal"])
    assert cmds[-1] == [
        "poetry",
        "install",
        "--with",
        "dev",
        "--extras",
        "minimal",
    ]

    data = tomllib.loads(Path("pyproject.toml").read_text())
    extras = list(data.get("project", {}).get("optional-dependencies", {}).keys())
    expected = [e for e in extras if e != "minimal"]

    cmds = _run(monkeypatch, [])
    assert cmds[-1] == [
        "poetry",
        "install",
        "--with",
        "dev",
        "--extras",
        *expected,
    ]
