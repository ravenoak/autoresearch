import types
import pytest
from autoresearch.orchestration import metrics


def _fake_time_gen():
    t = {'v': 0}

    def fake():
        t['v'] += 1
        return t['v']
    return fake


@pytest.mark.parametrize(
    "records",
    [
        [(1, 2), (3, 4)],
        [(5, 1)],
    ],
)
def test_metrics_summary(monkeypatch, records):
    fake_time = _fake_time_gen()
    monkeypatch.setattr(metrics, "time", types.SimpleNamespace(time=fake_time))

    m = metrics.OrchestrationMetrics()
    total_in = total_out = 0
    for tokens_in, tokens_out in records:
        m.start_cycle()
        m.record_tokens("agent", tokens_in, tokens_out)
        m.end_cycle()
        total_in += tokens_in
        total_out += tokens_out

    summary = m.get_summary()
    assert summary["cycles_completed"] == len(records)
    assert summary["total_tokens"]["input"] == total_in
    assert summary["total_tokens"]["output"] == total_out
    assert summary["total_tokens"]["total"] == total_in + total_out
