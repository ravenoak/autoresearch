"""Step definitions for the installer feature."""

from __future__ import annotations

import sys
from pathlib import Path
import tomllib

from pytest_bdd import scenario, given, when, then

import importlib.util

INSTALLER_PATH = Path(__file__).resolve().parents[3] / "scripts" / "installer.py"
spec = importlib.util.spec_from_file_location("installer", INSTALLER_PATH)
installer = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(installer)  # type: ignore


def _run_installer(monkeypatch, args):
    cmds = []
    monkeypatch.setattr(installer, "run", lambda cmd: cmds.append(cmd))
    monkeypatch.setattr(sys, "argv", ["installer.py"] + args)
    monkeypatch.chdir(Path(__file__).resolve().parents[3])
    installer.main()
    return cmds


@given('the installer was run with "--minimal" previously')
def installer_run_minimal_first(monkeypatch, bdd_context):
    _run_installer(monkeypatch, ["--minimal"])


@when('I run the installer with "--minimal"')
def run_installer_minimal(monkeypatch, bdd_context):
    bdd_context["cmds"] = _run_installer(monkeypatch, ["--minimal"])


@when('I run the installer without arguments')
def run_installer_default(monkeypatch, bdd_context):
    bdd_context["cmds"] = _run_installer(monkeypatch, [])


@then('only the minimal extra should be installed')
def check_minimal(bdd_context):
    cmd = bdd_context["cmds"][-1]
    assert cmd[:5] == ["poetry", "install", "--with", "dev", "--extras"]
    assert cmd[5:] == ["minimal"]


@then('all extras except minimal should be installed')
def check_all_extras(bdd_context):
    data = tomllib.loads(Path("pyproject.toml").read_text())
    extras = list(data.get("project", {}).get("optional-dependencies", {}).keys())
    expected = [e for e in extras if e != "minimal"]
    cmd = bdd_context["cmds"][-1]
    assert cmd[:5] == ["poetry", "install", "--with", "dev", "--extras"]
    assert cmd[5:] == expected


@scenario("../features/installer.feature", "Minimal installation")
def test_minimal_install():
    pass


@scenario("../features/installer.feature", "Automatic dependency resolution")
def test_auto_resolution():
    pass


@scenario("../features/installer.feature", "Upgrade from minimal to full installation")
def test_upgrade_install():
    pass
