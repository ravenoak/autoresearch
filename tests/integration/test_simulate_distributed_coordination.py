# mypy: ignore-errors
"""Regression test for distributed coordination simulation."""

from __future__ import annotations

import json
import re

from scripts import simulate_distributed_coordination as sim_dc


def test_simulate_distributed_coordination_baseline(capsys) -> None:
    """The simulation processes tasks and reports metrics."""

    sim_dc.main(workers=2, tasks=100, loops=5)
    lines = capsys.readouterr().out.strip().splitlines()
    text_line = next(line for line in lines if line.startswith("Processed"))
    metrics = json.loads(lines[-1])
    match = re.search(r"Processed (\d+) tasks in ([0-9.]+)s with (\d+) workers", text_line)
    assert match, text_line
    tasks = int(match.group(1))
    duration = float(match.group(2))
    workers = int(match.group(3))
    assert tasks == 500
    assert workers == 2
    assert duration > 0.0
    assert metrics["throughput"] > 0
