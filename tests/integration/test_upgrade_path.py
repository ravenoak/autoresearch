import os
import runpy
import subprocess
import sys
import shutil
from pathlib import Path


SCRIPT = Path(__file__).parents[2] / "scripts" / "upgrade.py"


def run_upgrade(tmp_path: Path, poetry_env: bool):
    if poetry_env:
        (tmp_path / "pyproject.toml").write_text("")

    calls = []

    def fake_call(cmd, *a, **k):
        calls.append(cmd)

    def fake_which(name):
        if poetry_env and name == "poetry":
            return "poetry"
        return None

    orig_call = subprocess.check_call
    orig_which = shutil.which
    subprocess.check_call = fake_call  # type: ignore
    shutil.which = fake_which  # type: ignore
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        runpy.run_path(str(SCRIPT))
    finally:
        os.chdir(cwd)
        subprocess.check_call = orig_call  # type: ignore
        shutil.which = orig_which  # type: ignore
    return calls


def test_upgrade_with_poetry(tmp_path):
    calls = run_upgrade(tmp_path, poetry_env=True)
    assert ["poetry", "update", "autoresearch"] in calls


def test_upgrade_with_pip(tmp_path):
    calls = run_upgrade(tmp_path, poetry_env=False)
    expected = [sys.executable, "-m", "pip", "install", "-U", "autoresearch"]
    assert expected in calls
