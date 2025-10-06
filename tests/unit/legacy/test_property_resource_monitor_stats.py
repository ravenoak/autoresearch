# mypy: ignore-errors
"""Property tests for resource monitor statistical formulas."""

from __future__ import annotations

import math

import numpy as np
from hypothesis import HealthCheck, given, settings, strategies as st


def stats(values: list[float], q: float) -> tuple[float, float, float, float]:
    """Return mean, variance, quantile, and standard error."""
    n = len(values)
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    data = sorted(values)
    k = (n - 1) * q
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        q_val = data[int(k)]
    else:
        q_val = data[f] * (c - k) + data[c] * (k - f)
    se = math.sqrt(var / n)
    return mean, var, q_val, se


@given(
    st.lists(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=50,
    )
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_statistics_match_numpy(values: list[float]) -> None:
    """Ensure custom stats align with NumPy implementations."""
    mean, var, q_val, se = stats(values, 0.95)
    np_mean = float(np.mean(values))
    np_var = float(np.var(values, ddof=1))
    np_q = float(np.quantile(values, 0.95))
    np_se = float(np.std(values, ddof=1) / math.sqrt(len(values)))
    assert math.isclose(mean, np_mean, rel_tol=1e-7, abs_tol=1e-7)
    assert math.isclose(var, np_var, rel_tol=1e-7, abs_tol=1e-7)
    assert math.isclose(q_val, np_q, rel_tol=1e-7, abs_tol=1e-7)
    assert math.isclose(se, np_se, rel_tol=1e-7, abs_tol=1e-7)
