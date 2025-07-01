import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_token_regression.py"


def test_token_regression_script():
    result = subprocess.run([
        "poetry",
        "run",
        "python",
        str(SCRIPT),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
