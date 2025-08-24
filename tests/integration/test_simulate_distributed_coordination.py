"""Regression test for distributed coordination simulation."""

from __future__ import annotations

import re

from scripts import simulate_distributed_coordination as sim_dc


def test_simulate_distributed_coordination_baseline(capsys) -> None:
    """The simulation processes a fixed number of tasks."""

    sim_dc.main(workers=2, tasks=100)
    output = capsys.readouterr().out.strip()
    match = re.search(r"Processed (\d+) tasks in ([0-9.]+)s with (\d+) workers", output)
    assert match, output
    tasks = int(match.group(1))
    duration = float(match.group(2))
    workers = int(match.group(3))
    assert tasks == 1000
    assert workers == 2
    assert duration > 0.0
    throughput = tasks / duration
    assert throughput > 1000
