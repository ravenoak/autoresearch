"""Validate streaming webhook simulation against reliability bound.

See :mod:`docs.algorithms.api_streaming` for proof sketch.
"""

from scripts.streaming_webhook_sim import simulate_webhook


def test_simulated_success_matches_bound() -> None:
    """Simulation approximates reliability bound from the proof sketch."""

    success_prob = 0.3
    retries = 4
    trials = 2000
    result = simulate_webhook(success_prob, retries, timeout=1.0, trials=trials, seed=42)
    bound = 1 - (1 - success_prob) ** (retries + 1)
    assert abs(result.success_rate - bound) < 0.05
    assert result.avg_attempts <= retries + 1
