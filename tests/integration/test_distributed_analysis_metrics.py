# mypy: ignore-errors
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest

from autoresearch.distributed.broker import AgentResultMessage
from tests.optional_imports import import_or_skip


@pytest.mark.requires_distributed
@pytest.mark.requires_analysis
def test_redis_metrics_dataframe(monkeypatch: pytest.MonkeyPatch) -> None:
    """RedisBroker publishes messages and Polars summarizes metrics."""
    import_or_skip("redis")
    import_or_skip("fakeredis")
    import_or_skip("polars")
    import fakeredis
    import redis
    from autoresearch.distributed.broker import RedisBroker
    from autoresearch.data_analysis import metrics_dataframe

    fake: fakeredis.FakeRedis = fakeredis.FakeRedis()

    class DummyRedis:
        @classmethod
        def from_url(cls, *args: Any, **kwargs: Any) -> fakeredis.FakeRedis:
            return fake

    monkeypatch.setattr(redis, "Redis", DummyRedis)
    broker = RedisBroker()
    message: AgentResultMessage = {
        "action": "agent_result",
        "agent": "worker",
        "result": {"metrics": {"latency": 0.1}},
        "pid": 1234,
    }
    broker.publish(message)
    broker.shutdown()

    monkeypatch.setattr(
        "autoresearch.data_analysis.ConfigLoader",
        lambda: SimpleNamespace(
            config=SimpleNamespace(analysis=SimpleNamespace(polars_enabled=True))
        ),
    )

    df: Any = metrics_dataframe({"agent_timings": {"worker": [0.1, 0.2, 0.3]}})
    first_row = cast(tuple[Any, ...], df.row(0))
    assert first_row[0] == "worker"
    assert pytest.approx(first_row[1], rel=1e-3) == 0.2
    assert first_row[2] == 3
