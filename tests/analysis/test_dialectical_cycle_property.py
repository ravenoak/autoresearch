"""Property-based tests for dialectical coordination.

Verifies that increasing the fact-checker weight ``alpha`` never decreases
mean convergence of the synthesized belief.
"""

from __future__ import annotations

import random

import pytest
from hypothesis import assume, given, settings, strategies as st

from tests.analysis.dialectical_cycle_analysis import simulate


@pytest.mark.slow
@settings(deadline=None)
@given(
    alphas=st.tuples(
        st.floats(min_value=0.1, max_value=0.9),
        st.floats(min_value=0.1, max_value=0.9),
    ),
    loops=st.integers(min_value=1, max_value=8),
)
def test_mean_monotonic_in_alpha(alphas: tuple[float, float], loops: int) -> None:
    """Ensure larger ``alpha`` values pull the mean closer to the ground truth."""
    alpha1, alpha2 = alphas
    assume(alpha2 > alpha1)
    random.seed(0)
    res1 = simulate(alpha=alpha1, loops=loops, trials=50)
    random.seed(0)
    res2 = simulate(alpha=alpha2, loops=loops, trials=50)
    assert res2["mean_final"] >= res1["mean_final"]
