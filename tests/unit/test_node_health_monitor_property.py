from pathlib import Path
import importlib.util

from hypothesis import given, strategies as st
from prometheus_client import CollectorRegistry
import pytest

spec = importlib.util.spec_from_file_location(
    "node_health",
    Path(__file__).resolve().parents[2] / "src" / "autoresearch" / "monitor" / "node_health.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load node_health module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
NodeHealthMonitor = module.NodeHealthMonitor  # type: ignore[attr-defined]


pytestmark = [pytest.mark.requires_distributed, pytest.mark.redis]


@given(redis_up=st.booleans(), ray_up=st.booleans())
def test_check_once_updates_gauges(redis_up: bool, ray_up: bool) -> None:
    """Property-based test for gauge updates in NodeHealthMonitor."""
    registry = CollectorRegistry()
    monitor = NodeHealthMonitor(port=None, registry=registry)
    monitor._check_redis = lambda: redis_up  # type: ignore[method-assign]
    monitor._check_ray = lambda: ray_up  # type: ignore[method-assign]

    monitor.check_once()

    assert monitor.redis_gauge._value.get() == int(redis_up)
    assert monitor.ray_gauge._value.get() == int(ray_up)
    assert monitor.health_gauge._value.get() == int(redis_up and ray_up)
