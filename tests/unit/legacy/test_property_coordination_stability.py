# mypy: ignore-errors
from __future__ import annotations

from hypothesis import given, strategies as st


def iterate(alpha: float, g: float, steps: int) -> float:
    b_s = b_c = b_f = 0.0
    for _ in range(steps):
        new_b_s = (b_s + b_c + b_f) / 3
        new_b_c = b_s
        new_b_f = b_s + alpha * (g - b_s)
        b_s, b_c, b_f = new_b_s, new_b_c, new_b_f
    return b_s


@given(
    alpha=st.floats(min_value=0.01, max_value=0.99),
    g=st.floats(-1.0, 1.0),
    steps=st.integers(min_value=1, max_value=5),
)
def test_error_bounded(alpha: float, g: float, steps: int) -> None:
    initial = abs(g)
    final = abs(g - iterate(alpha, g, steps))
    if steps == 1:
        assert final == initial
    else:
        bound = initial * (1 - alpha / 3)
        assert final <= bound + 1e-6
