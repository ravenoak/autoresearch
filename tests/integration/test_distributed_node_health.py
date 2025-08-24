import sys
import types
from pathlib import Path

import pytest
from prometheus_client import CollectorRegistry

package = types.ModuleType("autoresearch.monitor")
package.__path__ = [str(Path(__file__).resolve().parents[2] / "src" / "autoresearch" / "monitor")]
sys.modules.setdefault("autoresearch.monitor", package)
from autoresearch.monitor.node_health import NodeHealthMonitor  # noqa: E402

pytestmark = [pytest.mark.slow, pytest.mark.requires_distributed]


class DummyRedis:
    def ping(self) -> bool:  # pragma: no cover - simple
        return True

    def close(self) -> None:  # pragma: no cover - no-op
        pass


class DummyRay:
    @staticmethod
    def init(**_: object) -> None:  # pragma: no cover - stub
        pass

    @staticmethod
    def cluster_resources() -> dict[str, int]:  # pragma: no cover - stub
        return {"CPU": 1}

    @staticmethod
    def shutdown() -> None:  # pragma: no cover - stub
        pass


def test_node_health_monitor(monkeypatch: pytest.MonkeyPatch, free_tcp_port: int) -> None:
    import redis

    monkeypatch.setattr(redis.Redis, "from_url", lambda url: DummyRedis())
    monkeypatch.setitem(sys.modules, "ray", DummyRay)
    registry = CollectorRegistry()
    monitor = NodeHealthMonitor(
        redis_url="redis://localhost:6379/0",
        ray_address="auto",
        port=free_tcp_port,
        interval=0.1,
        registry=registry,
    )
    monitor.check_once()
    assert registry.get_sample_value("autoresearch_redis_up") == 1.0
    assert registry.get_sample_value("autoresearch_ray_up") == 1.0
    assert registry.get_sample_value("autoresearch_node_health") == 1.0
