import os
import runpy
import sys
from pathlib import Path

import pytest
from typing import Any, Sequence
from unittest.mock import patch


SCRIPT = Path(__file__).parents[2] / "scripts" / "upgrade.py"


def run_upgrade(tmp_path: Path, poetry_env: bool) -> list[Sequence[Any] | Any]:
    if poetry_env:
        (tmp_path / "pyproject.toml").write_text("")

    calls: list[Sequence[Any] | Any] = []

    def fake_call(cmd: Sequence[Any] | Any, *args: Any, **kwargs: Any) -> None:
        calls.append(cmd)

    def fake_which(name: str) -> str | None:
        if poetry_env and name == "poetry":
            return "poetry"
        return None

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with patch("subprocess.check_call", side_effect=fake_call), patch(
            "shutil.which", side_effect=fake_which
        ):
            runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        os.chdir(cwd)
    return calls


@pytest.mark.slow
def test_upgrade_with_poetry(tmp_path):
    calls = run_upgrade(tmp_path, poetry_env=True)
    assert ["poetry", "update", "autoresearch"] in calls


@pytest.mark.slow
def test_upgrade_with_pip(tmp_path):
    calls = run_upgrade(tmp_path, poetry_env=False)
    expected = [sys.executable, "-m", "pip", "install", "-U", "autoresearch"]
    assert expected in calls
