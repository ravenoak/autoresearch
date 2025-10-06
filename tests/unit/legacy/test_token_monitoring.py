# mypy: ignore-errors
import json
from pathlib import Path
from typing import cast

from autoresearch.orchestration.metrics import OrchestrationMetrics


def test_record_and_regression(tmp_path: Path) -> None:
    metrics: OrchestrationMetrics = OrchestrationMetrics()
    metrics.record_tokens("A", 2, 3)
    metrics.record_tokens("B", 1, 1)

    metrics_path: Path = tmp_path / "metrics.json"
    baseline_path: Path = tmp_path / "baseline.json"

    # baseline lower than current total (7)
    baseline_path.write_text(json.dumps({"q": 5}))

    metrics.record_query_tokens("q", metrics_path)
    saved: dict[str, int] = cast(dict[str, int], json.loads(metrics_path.read_text()))
    assert saved["q"] == 7

    assert metrics.check_query_regression("q", baseline_path) is True
    assert metrics.check_query_regression("q", baseline_path, threshold=2) is False
    assert metrics.check_query_regression("missing", baseline_path) is False
