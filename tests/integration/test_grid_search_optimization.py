from pathlib import Path

from autoresearch.search import Search


def test_optimize_weights_returns_better_score():
    data_path = Path(__file__).resolve().parents[1] / "data" / "eval" / "sample_eval.csv"
    data = Search.load_evaluation_data(data_path)

    baseline = Search.evaluate_weights((0.5, 0.3, 0.2), data)
    best, score = Search.optimize_weights(data, step=0.1)

    assert score >= baseline
    assert abs(sum(best) - 1.0) < 0.01
