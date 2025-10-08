# mypy: ignore-errors
"""Tests for the API routes compatibility shim."""

from autoresearch.api.routes import router
from autoresearch.config import ConfigLoader


def test_router_builds_correctly():
    """Test that the router is built correctly based on configuration."""
    # Test with monitoring disabled (default)
    config = ConfigLoader().load_config()
    assert not config.api.monitoring_enabled

    # The router should be built without the /metrics endpoint
    routes = [route.path for route in router.routes]
    assert "/metrics" not in routes
    assert "/config" in routes
    assert "/capabilities" in routes


def test_router_builds_with_monitoring_enabled(monkeypatch):
    """Test that the router includes /metrics when monitoring is enabled."""
    # Mock config to enable monitoring
    from autoresearch.config.models import ConfigModel

    mock_config = ConfigModel(api={"monitoring_enabled": True})
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: mock_config)

    # Import the module to trigger router rebuild
    import importlib
    import autoresearch.api.routes as routes_module
    importlib.reload(routes_module)

    # Check that the router now includes /metrics
    routes = [route.path for route in routes_module.router.routes]
    assert "/metrics" in routes
