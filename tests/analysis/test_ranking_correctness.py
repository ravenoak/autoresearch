"""Tests for ranking correctness simulation."""

from tests.analysis.ranking_correctness_analysis import run


def test_ranking_correctness() -> None:
    metrics = run()
    assert metrics["correctness"] == 1.0
