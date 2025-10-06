# mypy: ignore-errors
from types import MethodType

from hypothesis import given, strategies as st
from prometheus_client import CollectorRegistry
import pytest

from autoresearch.monitor.node_health import NodeHealthMonitor


pytestmark = [pytest.mark.requires_distributed, pytest.mark.redis]


@given(redis_up=st.booleans(), ray_up=st.booleans())
def test_check_once_updates_gauges(redis_up: bool, ray_up: bool) -> None:
    """Property-based test for gauge updates in NodeHealthMonitor."""
    registry = CollectorRegistry()
    monitor = NodeHealthMonitor(port=None, registry=registry)
    monitor._check_redis = MethodType(lambda self: redis_up, monitor)
    monitor._check_ray = MethodType(lambda self: ray_up, monitor)

    monitor.check_once()

    assert registry.get_sample_value("autoresearch_redis_up") == int(redis_up)
    assert registry.get_sample_value("autoresearch_ray_up") == int(ray_up)
    assert registry.get_sample_value("autoresearch_node_health") == int(
        redis_up and ray_up
    )
