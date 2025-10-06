# mypy: ignore-errors
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_token_regression.py"

pytestmark = pytest.mark.slow


def test_token_regression_script() -> None:
    result = subprocess.run([
        "poetry",
        "run",
        "python",
        str(SCRIPT),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
