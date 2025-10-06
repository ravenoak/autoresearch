# mypy: ignore-errors
import pytest

from autoresearch.search import Search

pytestmark = pytest.mark.requires_nlp


def test_optimize_weights_improves_score(sample_eval_data):
    data = sample_eval_data
    baseline = Search.evaluate_weights((0.5, 0.3, 0.2), data)
    best, score = Search.optimize_weights(data, step=0.1)
    assert score >= baseline
    assert abs(sum(best) - 1.0) < 0.01
