"""Step definitions for Metrics API behavior tests."""

from __future__ import annotations

from pytest_bdd import given, when, then, scenario, parsers

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from tests.behavior.context import BehaviorContext


@given("the API server is running")
def api_server_running(
    bdd_context: BehaviorContext,
    api_client,
    monkeypatch,
    temp_config,
    restore_environment,
) -> None:
    """Provide a configured API client for metrics tests."""

    cfg = ConfigModel(api=APIConfig())
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    bdd_context["client"] = api_client


@when("I request the metrics endpoint with authorization")
def request_metrics_authorized(
    bdd_context: BehaviorContext,
    monkeypatch,
    temp_config,
    restore_environment,
) -> None:
    """Request the metrics endpoint with proper permissions."""

    cfg = ConfigModel(api=APIConfig(api_key="secret"))
    cfg.api.role_permissions["user"] = ["metrics"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    client = bdd_context["client"]
    bdd_context["response"] = client.get(
        "/metrics", headers={"X-API-Key": "secret"}
    )


@when("I request the metrics endpoint")
def request_metrics_denied(
    bdd_context: BehaviorContext,
    monkeypatch,
    temp_config,
    restore_environment,
) -> None:
    """Request the metrics endpoint without necessary permissions."""

    cfg = ConfigModel(api=APIConfig())
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    client = bdd_context["client"]
    bdd_context["response"] = client.get("/metrics")


@then("the response status should be 200")
def check_status_ok(bdd_context: BehaviorContext) -> None:
    """Assert that the HTTP response was successful."""

    assert bdd_context["response"].status_code == 200


@then("the response status should be 403")
def check_status_forbidden(bdd_context: BehaviorContext) -> None:
    """Assert that access was forbidden."""

    assert bdd_context["response"].status_code == 403


@then(parsers.parse('the response body should contain "{text}"'))
def check_body_contains(text: str, bdd_context: BehaviorContext) -> None:
    """Verify that the metrics output includes the expected metric name."""

    assert text in bdd_context["response"].text


@scenario(
    "../features/api_metrics.feature",
    "Retrieve Prometheus metrics",
)
def test_retrieve_metrics() -> None:
    """Authorized clients can retrieve metrics."""
    return


@scenario(
    "../features/api_metrics.feature",
    "Metrics endpoint without permission",
)
def test_metrics_no_permission() -> None:
    """Unauthorized access to metrics endpoint is forbidden."""
    return
