import re
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_ranking_convergence_script() -> None:
    """The ranking convergence simulation reports completion."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "ranking_convergence.py"
    result = subprocess.run(
        [sys.executable, str(script), "--items", "3"],
        capture_output=True,
        text=True,
        check=True,
    )
    match = re.search(r"converged in (\d+(?:\.\d+)?) steps", result.stdout)
    assert match, result.stdout
