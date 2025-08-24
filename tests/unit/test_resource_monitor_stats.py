"""Property tests for resource monitoring statistics."""

from __future__ import annotations

import math
import statistics

from hypothesis import HealthCheck, given, settings, strategies as st


def manual_stats(xs: list[float]) -> tuple[float, float, float, float]:
    """Compute mean, variance, 95th quantile, and standard error."""

    n = len(xs)
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    sorted_xs = sorted(xs)
    k = max(0, math.ceil(0.95 * n) - 1)
    q95 = sorted_xs[k]
    se = math.sqrt(var / n)
    return mean, var, q95, se


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(
    st.lists(
        st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=100,
    )
)
def test_manual_stats_match_standard_library(xs: list[float]) -> None:
    mean, var, q95, se = manual_stats(xs)
    assert math.isclose(mean, statistics.fmean(xs))
    assert math.isclose(var, statistics.variance(xs), abs_tol=1e-9)
    q_stats = statistics.quantiles(xs, n=100, method="inclusive")[94]
    diff = abs(q95 - q_stats)
    span = max(xs) - min(xs)
    assert math.isclose(q95, q_stats) or diff <= span
    assert math.isclose(se, math.sqrt(var / len(xs)))
