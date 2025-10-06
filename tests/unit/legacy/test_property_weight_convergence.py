# mypy: ignore-errors
import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from autoresearch.search import Search

pytestmark = pytest.mark.requires_nlp


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(step=st.floats(min_value=0.05, max_value=0.2))
def test_ndcg_monotonic_with_step(step, sample_eval_data):
    data = sample_eval_data
    coarse = Search.tune_weights(data, step=step)
    coarse_score = Search.evaluate_weights(coarse, data)
    fine = Search.tune_weights(data, step=step / 2)
    fine_score = Search.evaluate_weights(fine, data)
    assert fine_score >= coarse_score
