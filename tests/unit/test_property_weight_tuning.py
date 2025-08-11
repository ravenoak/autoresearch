import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from autoresearch.search import Search


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(step=st.floats(min_value=0.05, max_value=0.3))
def test_tune_weights_improves_ndcg(step, sample_eval_data):
    data = sample_eval_data
    baseline = Search.evaluate_weights((0.5, 0.3, 0.2), data)
    tuned = Search.tune_weights(data, step=step)
    assert pytest.approx(sum(tuned), 0.001) == 1.0
    tuned_score = Search.evaluate_weights(tuned, data)
    assert tuned_score >= baseline
