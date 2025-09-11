import pytest

from autoresearch.search.ranking import combine_scores


def test_combine_scores_weighted_sum() -> None:
    """combine_scores applies weights after normalizing components."""
    bm25 = [3.0, 1.0]
    semantic = [0.8, 0.2]
    credibility = [0.9, 0.5]
    weights = (0.5, 0.3, 0.2)
    scores = combine_scores(bm25, semantic, credibility, weights)
    assert scores == pytest.approx([1.0, 0.35], abs=0.01)
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_combine_scores_invalid_weights() -> None:
    """Invalid weight sums raise ValueError."""
    with pytest.raises(ValueError):
        combine_scores([1.0], [1.0], [1.0], (0.6, 0.3, 0.2))
