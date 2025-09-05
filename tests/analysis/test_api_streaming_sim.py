"""Tests for API streaming simulation."""

from tests.analysis.api_streaming_analysis import run


def test_api_streaming_sim() -> None:
    metrics = run()
    assert metrics["received"] == metrics["expected"]
    assert metrics["heartbeats"] >= 1
    assert metrics["success"]
