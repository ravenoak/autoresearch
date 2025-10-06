"""Tests for the source credibility simulation script."""
from statistics import mean

from scripts.simulate_source_credibility import score_dataset


def test_scores_within_bounds() -> None:
    for _, score in score_dataset():
        assert 0.0 <= score <= 1.0


def test_scores_monotonic_with_labels() -> None:
    pairs = score_dataset()
    positives = [s for label, s in pairs if label == 1]
    negatives = [s for label, s in pairs if label == 0]
    assert min(positives) > max(negatives)
    assert mean(positives) > mean(negatives)
