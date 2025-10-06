# mypy: ignore-errors
"""Regression tests for distributed performance simulation script."""

import importlib.util
import json
import subprocess
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "distributed_perf_sim", Path(__file__).parents[2] / "scripts" / "distributed_perf_sim.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load distributed_perf_sim module")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_latency_decreases_with_workers() -> None:
    """Adding workers reduces simulated latency."""
    results = MODULE.simulate(3, 2.0, 3.0, 0.0)
    assert results[0]["latency_s"] > results[-1]["latency_s"]


def test_cli_execution(tmp_path: Path) -> None:
    """CLI invocation returns JSON and writes a plot."""
    script = Path(__file__).parents[2] / "scripts" / "distributed_perf_sim.py"
    out = subprocess.check_output(
        [
            "uv",
            "run",
            str(script),
            "--max-workers",
            "2",
            "--arrival-rate",
            "1",
            "--service-rate",
            "2",
            "--output",
            str(tmp_path / "plot.svg"),
        ]
    )
    data = json.loads(out.decode())
    assert data[0]["throughput"] == 1
    assert (tmp_path / "plot.svg").exists()


def test_cli_requires_arguments() -> None:
    """Missing flags produce a helpful error."""
    script = Path(__file__).parents[2] / "scripts" / "distributed_perf_sim.py"
    proc = subprocess.run(["uv", "run", str(script)], stderr=subprocess.PIPE)
    assert proc.returncode != 0
    assert b"required" in proc.stderr
