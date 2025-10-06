# mypy: ignore-errors
import json
import subprocess
from pathlib import Path


def test_orchestrator_perf_metrics() -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "orchestrator_perf_sim.py"
    cmd = [
        "uv",
        "run",
        str(script),
        "--workers",
        "2",
        "--arrival-rate",
        "3",
        "--service-rate",
        "5",
        "--tasks",
        "50",
        "--mem-per-task",
        "0.5",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    assert 0 < data["utilization"] < 1
    assert data["avg_queue_length"] >= 0
    assert data["expected_memory"] == 25.0
