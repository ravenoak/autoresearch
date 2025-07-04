import json
from autoresearch.orchestration import metrics


def test_record_tokens_and_regression(tmp_path):
    m = metrics.OrchestrationMetrics()
    m.record_tokens("A", 2, 3)
    file_path = tmp_path / "tok.json"
    m.record_query_tokens("q1", file_path)
    data = json.loads(file_path.read_text())
    assert data["q1"] == 5

    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"q1": 4}))
    assert m.check_query_regression("q1", baseline, threshold=0) is True
    assert not m.check_query_regression("missing", baseline)
