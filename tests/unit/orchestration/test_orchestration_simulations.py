import sys
from unittest.mock import patch

from scripts.orchestration_sim import (
    circuit_breaker_sim,
    main,
    parallel_execution_sim,
)
import pytest


def test_circuit_breaker_sim_is_deterministic() -> None:
    assert circuit_breaker_sim() == circuit_breaker_sim()


def test_parallel_execution_sim_is_deterministic() -> None:
    first = parallel_execution_sim()
    second = parallel_execution_sim()
    assert first == second
    assert set(first.keys()) == {"A", "B", "C"}


def test_cli_runs_modes(capsys: pytest.CaptureFixture[str]) -> None:
    with patch.object(sys, "argv", ["orchestration_sim.py", "circuit"]):
        main()
        assert "open" in capsys.readouterr().out
    with patch.object(sys, "argv", ["orchestration_sim.py", "parallel"]):
        main()
        assert "claim-A" in capsys.readouterr().out
