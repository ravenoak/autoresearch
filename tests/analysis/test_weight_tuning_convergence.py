from tests.analysis.weight_tuning_analysis import simulate_convergence


def test_weight_convergence_monotonic() -> None:
    metrics = simulate_convergence(0.1)
    ndcgs = [s["ndcg"] for s in metrics["steps"]]
    assert ndcgs == sorted(ndcgs)
