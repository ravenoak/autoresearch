from typing import cast

from tests.analysis.weight_tuning_analysis import simulate_convergence


def test_weight_convergence_monotonic() -> None:
    metrics = simulate_convergence(0.1)
    steps = cast(list[dict[str, float]], metrics["steps"])
    ndcgs = [s["ndcg"] for s in steps]
    assert ndcgs == sorted(ndcgs)
