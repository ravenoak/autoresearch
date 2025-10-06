from __future__ import annotations

import pytest
from hypothesis import given, strategies as st


def iterate(alpha: float, g: float, steps: int = 3) -> float:
    b_s = b_c = b_f = g
    for _ in range(steps):
        new_b_s = (b_s + b_c + b_f) / 3
        new_b_c = b_s
        new_b_f = b_s + alpha * (g - b_s)
        b_s, b_c, b_f = new_b_s, new_b_c, new_b_f
    return b_s


@given(alpha=st.floats(min_value=0.0, max_value=1.0), g=st.floats(-1.0, 1.0))
def test_ground_truth_fixed_point(alpha: float, g: float) -> None:
    """If beliefs match the ground truth, they remain unchanged."""
    final = iterate(alpha, g, steps=3)
    assert final == pytest.approx(g)
