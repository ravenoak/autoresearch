import subprocess
import sys
from pathlib import Path

import tomllib
from autoresearch.search import Search


def test_optimize_script_updates_weights(tmp_path):
    dataset = Path(__file__).resolve().parents[1] / "data" / "eval" / "sample_eval.csv"
    cfg = tmp_path / "cfg.toml"
    cfg.write_text(
        """[search]\nsemantic_similarity_weight = 0.5\nbm25_weight = 0.3\nsource_credibility_weight = 0.2\n"""
    )

    baseline_data = Search.load_evaluation_data(dataset)
    baseline = Search.evaluate_weights((0.5, 0.3, 0.2), baseline_data)

    script = Path(__file__).resolve().parents[2] / "scripts" / "optimize_search_weights.py"
    subprocess.run(
        [sys.executable, str(script), str(dataset), str(cfg)],
        check=True,
    )

    tuned = tomllib.loads(cfg.read_text())["search"]
    tuned_weights = (
        tuned["semantic_similarity_weight"],
        tuned["bm25_weight"],
        tuned["source_credibility_weight"],
    )
    tuned_score = Search.evaluate_weights(tuned_weights, baseline_data)

    assert tuned_score >= baseline
    assert abs(sum(tuned_weights) - 1.0) < 0.01
