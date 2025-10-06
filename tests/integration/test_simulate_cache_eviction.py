# mypy: ignore-errors
"""Regression test for cache eviction simulation."""

from __future__ import annotations

import random
import re

from scripts import simulate_cache_eviction as sim_ce


def test_simulate_cache_eviction_baseline(capsys) -> None:
    """Cache usage stays within the configured budget."""

    random.seed(0)
    sim_ce.simulate(1024, 50)
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[-1] == "final memory 1018/1024"
    for line in lines[:-1]:
        match = re.search(r"total=(\d+)", line)
        assert match and int(match.group(1)) <= 1024
