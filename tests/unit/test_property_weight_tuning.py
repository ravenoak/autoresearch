import pytest
from pathlib import Path
from hypothesis import given, strategies as st

from autoresearch.search import Search


def load_data() -> dict:
    base = Path(__file__).resolve().parents[1]
    path = base / "data" / "eval" / "sample_eval.csv"
    return Search.load_evaluation_data(path)


@given(st.floats(min_value=0.05, max_value=0.3))
def test_tune_weights_improves_ndcg(step):
    data = load_data()
    baseline = Search.evaluate_weights((0.5, 0.3, 0.2), data)
    tuned = Search.tune_weights(data, step=step)
    assert pytest.approx(sum(tuned), 0.001) == 1.0
    tuned_score = Search.evaluate_weights(tuned, data)
    assert tuned_score >= baseline
