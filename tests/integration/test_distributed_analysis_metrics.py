from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests.optional_imports import import_or_skip


@pytest.mark.requires_distributed
@pytest.mark.requires_analysis
def test_redis_metrics_dataframe(monkeypatch):
    """RedisBroker publishes messages and Polars summarizes metrics."""
    import_or_skip("redis")
    import_or_skip("fakeredis")
    import_or_skip("polars")
    import fakeredis
    import redis
    from autoresearch.distributed.broker import RedisBroker
    from autoresearch.data_analysis import metrics_dataframe

    fake = fakeredis.FakeRedis()

    class DummyRedis:
        @classmethod
        def from_url(cls, *args, **kwargs):
            return fake

    monkeypatch.setattr(redis, "Redis", DummyRedis)
    broker = RedisBroker()
    broker.publish({"val": 1})
    broker.shutdown()

    monkeypatch.setattr(
        "autoresearch.data_analysis.ConfigLoader",
        lambda: SimpleNamespace(
            config=SimpleNamespace(analysis=SimpleNamespace(polars_enabled=True))
        ),
    )

    df = metrics_dataframe({"agent_timings": {"worker": [0.1, 0.2, 0.3]}})
    row = df.rows()[0]
    assert row[0] == "worker"
    assert pytest.approx(row[1], rel=1e-3) == 0.2
    assert row[2] == 3
