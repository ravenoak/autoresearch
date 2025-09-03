"""Step definitions for API edge case scenarios."""

from pytest_bdd import scenario, given, when, then
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader


@given("the API server is running")
def api_server_running(test_context, api_client):
    """Store an API client for requests."""
    test_context["client"] = api_client


@when("I send invalid JSON to the API")
def send_invalid_json(test_context):
    """Post malformed JSON payload to the API."""
    client = test_context["client"]
    resp = client.post(
        "/query",
        data="{invalid",
        headers={"Content-Type": "application/json"},
    )
    test_context["response"] = resp


@when("I request the metrics endpoint")
def request_metrics(test_context, monkeypatch):
    """Request metrics without proper permissions."""
    cfg = ConfigModel()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    client = test_context["client"]
    resp = client.get("/metrics")
    test_context["response"] = resp


@then("the response status should be 422")
def assert_status_422(test_context):
    """Ensure the API returned a 422 status code."""
    resp = test_context["response"]
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data


@then("the response status should be 403")
def assert_status_403(test_context):
    """Ensure the API returned a 403 status code."""
    resp = test_context["response"]
    assert resp.status_code == 403
    data = resp.json()
    assert "detail" in data


@scenario("../features/api_edge_cases.feature", "Invalid JSON returns 422")
def test_invalid_json():
    """Scenario: invalid JSON payload is rejected."""
    pass


@scenario(
    "../features/api_edge_cases.feature",
    "Permission denied for metrics endpoint",
)
def test_permission_denied_metrics():
    """Scenario: accessing metrics without permissions fails."""
    pass
